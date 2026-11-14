import json
import logging
import re
import time
import requests
import config

log = logging.getLogger("GeminiClient")

SYSTEM_PROMPT = """\
You write SystemVerilog (IEEE 1800-2012) for Cadence Incisive irun 15.20 (-sv).
Every rule below comes from a real failure on this exact toolchain.

OUTPUT
- Emit ONE ```systemverilog code block and nothing else.
- First line of every file is `timescale 1ns/1ps -- never `systemverilog.
- Design files are .v; verification files are .sv.
- Emit only the file you were asked for. Never redeclare the interface, the
  coverage module, or the DUT -- they are compiled separately (DUPUNI error).

LANGUAGE
- Use logic, not reg/wire, in .sv files.
- ALL declarations go at the TOP of a begin...end block, before any statement.
  A declaration after a statement is fatal (*E,MISEXX).
- No `inside` operator; use (a==x || a==y).
- No packages, no imports. Each file is self-contained.
- If you use classes: rand logic (never rand bit).

COVERGROUPS (irun 15.20 is strict here)
- A covergroup MUST live inside a module. One at file/compilation-unit scope
  is fatal (*E,UPITEM), and `ref` arguments are rejected there (*E,CBYREF).
- A module-scoped covergroup takes NO arguments -- it reads the module's ports
  directly. That is also why it may name those ports in its sampling event.
- Label EVERY coverpoint and EVERY cross (*E,ECGECL otherwise):
      sig_cp : coverpoint sig { bins lo = {0}; }
      a_b_x  : cross a_cp, b_cp;
- Never put `iff` on a bins statement; `iff` belongs on the coverpoint.
- Transition bins use CONSTANTS only: bins wrap = (15 => 0);
  A coverpoint containing transition bins must NOT appear in a cross.
- `small`, `medium`, `large` are Verilog keywords -- never use them as names.
- Inside a cross that defines its own bins, `= default` is illegal (*E,ECBNOD).

"""


class GeminiClient:

    def __init__(self):
        if not config.GEMINI_API_KEY:
            raise EnvironmentError("GEMINI_API_KEY not set.\n  export GEMINI_API_KEY='your-key'")
        self.url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{config.GEMINI_MODEL}:generateContent"
        )

    def generate_interface(self, prompt: str) -> str:
        return self._extract_sv(self._call_with_retry(prompt))

    def generate_coverage_model(self, prompt: str) -> str:
        return self._extract_sv(self._call_with_retry(prompt))

    def generate_testbench(self, prompt: str) -> str:
        return self._extract_sv(self._call_with_retry(prompt))

    def generate_top(self, prompt: str) -> str:
        return self._extract_sv(self._call_with_retry(prompt))

    def _call_with_retry(self, prompt: str, retries: int = 2) -> str:
        for attempt in range(1, retries + 2):
            try:
                return self._call_api(prompt)
            except RuntimeError as exc:
                log.warning(f"Attempt {attempt} failed: {exc}")
                if attempt <= retries:
                    wait = 65 * attempt
                    log.info(f"Retrying in {wait}s ...")
                    time.sleep(wait)
                else:
                    raise

    def _call_api(self, prompt: str) -> str:
        full = f"{SYSTEM_PROMPT}\n\n{prompt}"
        headers = {
            "Content-Type":   "application/json",
            "X-goog-api-key": config.GEMINI_API_KEY,
        }
        payload = {
            "contents": [{"parts": [{"text": full}]}],
            "generationConfig": {
                "maxOutputTokens": config.MAX_OUTPUT_TOKENS,
                "temperature":     config.TEMPERATURE,
                "topP":            0.95,
            },
        }
        log.info(f"  Gemini model={config.GEMINI_MODEL}  prompt={len(full)} chars")
        try:
            resp = requests.post(
                self.url, headers=headers,
                data=json.dumps(payload), timeout=config.API_TIMEOUT_SEC,
            )
        except requests.exceptions.Timeout:
            raise RuntimeError(f"API timed out after {config.API_TIMEOUT_SEC}s")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error: {e}")

        if resp.status_code == 429:
            raise RuntimeError("Rate-limited (429). Wait or switch model in config.py")
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:400]}")

        body  = resp.json()
        cands = body.get("candidates", [])
        if not cands:
            raise RuntimeError(f"No candidates: {body}")

        finish = cands[0].get("finishReason", "STOP")
        usage  = body.get("usageMetadata", {})
        log.info(
            f"  finishReason={finish}  "
            f"in={usage.get('promptTokenCount','?')}  "
            f"out={usage.get('candidatesTokenCount','?')} tokens"
        )
        if finish == "MAX_TOKENS":
            log.warning("Output cut at MAX_TOKENS -- increase MAX_OUTPUT_TOKENS in config.py")
        if finish == "SAFETY":
            raise RuntimeError("Blocked by safety filters.")

        return cands[0]["content"]["parts"][0]["text"]

    def _extract_sv(self, raw: str) -> str:
        # Normal case: opening and closing fences present
        for pattern in [
            r"```systemverilog\s*(.*?)\s*```",
            r"```(?:verilog|sv)\s*(.*?)\s*```",
            r"```\s*(.*?)\s*```",
        ]:
            m = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
            if m:
                code = m.group(1).strip()
                code = re.sub(r"^(?:systemverilog|verilog|sv)\s*\n", "", code, flags=re.IGNORECASE)
                return code.strip()

        # Truncated case: output was cut at MAX_TOKENS so closing ``` is absent.
        # Extract everything after the opening fence — even partial code compiles
        # better than returning the raw string that starts with "```systemverilog".
        for pattern in [
            r"```systemverilog\s*(.*)",
            r"```(?:verilog|sv)\s*(.*)",
            r"```\s*(.*)",
        ]:
            m = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
            if m:
                code = m.group(1).strip()
                code = re.sub(r"^(?:systemverilog|verilog|sv)\s*\n", "", code, flags=re.IGNORECASE)
                log.warning("Truncated code block (no closing ```) — using partial code; "
                            "increase MAX_OUTPUT_TOKENS in config.py")
                return code.strip()

        log.warning("No code block found -- using raw response")
        return raw.strip()
