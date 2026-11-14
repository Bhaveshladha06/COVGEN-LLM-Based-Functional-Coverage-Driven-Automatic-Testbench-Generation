#!/usr/bin/env python3
"""
kb_files.py -- explode the knowledge base into one readable file per design,
and fold edits back into the JSON.

WHY THIS EXISTS
    knowledge_base/coverage_kb.json holds all 87 entries on one line-noisy
    blob. That is the right shape for the pipeline (retriever.py loads it in
    one read) and the wrong shape for a human deciding whether an entry is any
    good. This tool gives you both: the JSON stays the single source of truth
    the pipeline reads, and `--export` writes a browsable mirror of it as one
    Markdown file per entry, grouped by category.

    The mirror is editable. Fix a coverage model in its .md file, run
    `--rebuild`, and the change lands in the JSON.

WHICH FILE IS THE TRUTH
    coverage_kb.json. Always. The exported files are a view of it until you
    explicitly run --rebuild, which is the only command that writes the JSON
    (and it backs the old one up first). If you edit both, --check tells you
    where they disagree before you overwrite anything.

USAGE
    python kb_files.py --export              # JSON  -> knowledge_base/entries/
    python kb_files.py --check               # report differences, change nothing
    python kb_files.py --rebuild             # files -> JSON  (writes a .bak first)
    python kb_files.py --export --id fifo_sync_8bit_001    # just one entry

FILE FORMAT
    knowledge_base/entries/<category>/<id>.md

        ---
        id: "fifo_sync_8bit_001"
        verified: false
        ...
        ---

        ## Requirement
        <the English requirement>

        ## RTL
        ```verilog
        ...
        ```

        ## Coverage model
        ```systemverilog
        ...
        ```

    Front-matter values are JSON-encoded (so "8" the string and 8 the number
    survive the trip unchanged). The three sections are plain text and fenced
    code, which is what you actually read.
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import config

ENTRIES_DIR = Path(config.KB_DIR) / "entries"
INDEX_FILE = ENTRIES_DIR / "_index.txt"

# Entry fields rendered as prose/code sections rather than front matter.
SECTION_FIELDS = [
    ("english_requirement", "Requirement", None),
    ("notes",               "Notes",       None),
    ("rtl",                 "RTL",         "verilog"),
    ("coverage_model",      "Coverage model", "systemverilog"),
]
SECTION_KEYS = {k for k, _, _ in SECTION_FIELDS}


# ---------------------------------------------------------------------------
# JSON <-> Markdown
# ---------------------------------------------------------------------------

def _slug(text: str) -> str:
    keep = [c if (c.isalnum() or c in "._-") else "_" for c in str(text)]
    return "".join(keep) or "unnamed"


def entry_to_markdown(entry: Dict[str, Any]) -> str:
    """Render one entry. Everything that is not a section field goes into the
    front matter, including keys this script has never seen -- so a future
    field added to the schema survives an export/rebuild round trip instead of
    being silently dropped."""
    fm: List[str] = []
    for key, value in entry.items():
        if key in SECTION_KEYS:
            continue
        if key == "design_context" and isinstance(value, dict):
            # Flattened so each fact sits on its own readable line.
            for sub, subval in value.items():
                fm.append(f"context.{sub}: {json.dumps(subval, ensure_ascii=False)}")
        else:
            fm.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")

    out = ["---", *fm, "---", ""]

    for key, heading, lang in SECTION_FIELDS:
        body = entry.get(key, "")
        body = "" if body is None else str(body)
        out.append(f"## {heading}")
        if lang:
            out.append(f"```{lang}")
            out.append(body.rstrip("\n"))
            out.append("```")
        else:
            out.append(body.rstrip("\n") if body.strip() else "(none)")
        out.append("")

    return "\n".join(out).rstrip("\n") + "\n"


def markdown_to_entry(text: str, source: str = "") -> Dict[str, Any]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{source}: file does not start with a '---' front-matter block")

    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ValueError(f"{source}: front-matter block is never closed with '---'")

    entry: Dict[str, Any] = {}
    context: Dict[str, Any] = {}
    for raw in lines[1:end]:
        if not raw.strip():
            continue
        if ":" not in raw:
            raise ValueError(f"{source}: front-matter line is not 'key: value': {raw!r}")
        key, _, value = raw.partition(":")
        key, value = key.strip(), value.strip()
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            # Tolerate a hand-typed bare string, the one edit a person is
            # likely to make by hand without thinking about JSON quoting.
            parsed = value
        if key.startswith("context."):
            context[key[len("context."):]] = parsed
        else:
            entry[key] = parsed
    if context:
        entry["design_context"] = context

    body = lines[end + 1:]
    for key, heading, lang in SECTION_FIELDS:
        entry[key] = _extract_section(body, heading, lang)

    return entry


def _extract_section(lines: List[str], heading: str, lang) -> str:
    """Pull one '## <heading>' section out of the body, unwrapping its code
    fence when it has one. Returns '' for a missing or '(none)' section."""
    start = None
    for i, line in enumerate(lines):
        if line.strip() == f"## {heading}":
            start = i + 1
            break
    if start is None:
        return ""

    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break

    chunk = lines[start:end]
    while chunk and not chunk[0].strip():
        chunk.pop(0)
    while chunk and not chunk[-1].strip():
        chunk.pop()

    if chunk and chunk[0].startswith("```"):
        chunk = chunk[1:]
        if chunk and chunk[-1].strip() == "```":
            chunk = chunk[:-1]

    body = "\n".join(chunk)
    return "" if body.strip() == "(none)" else body


# ---------------------------------------------------------------------------
# Load / save
# ---------------------------------------------------------------------------

def load_kb() -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    path = Path(config.KB_JSON)
    if not path.exists():
        sys.exit(f"Knowledge base not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "entries" in raw:
        return raw, raw["entries"]
    return {"entries": raw}, raw


def entry_path(entry: Dict[str, Any]) -> Path:
    return ENTRIES_DIR / _slug(entry.get("category", "uncategorised")) / f"{_slug(entry['id'])}.md"


def read_files() -> List[Dict[str, Any]]:
    """Read the exported entries back, preserving the JSON's original order via
    _index.txt so a rebuild does not silently reshuffle the corpus."""
    if not ENTRIES_DIR.exists():
        sys.exit(f"No exported files at {ENTRIES_DIR}. Run --export first.")

    on_disk = sorted(ENTRIES_DIR.rglob("*.md"))
    ordered: List[Path] = []
    if INDEX_FILE.exists():
        for line in INDEX_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = ENTRIES_DIR / line
            if p.exists():
                ordered.append(p)
            else:
                print(f"  [WARN] listed in _index.txt but missing on disk: {line}")
    # Files added by hand since the last export go on the end.
    ordered += [p for p in on_disk if p not in ordered]

    entries = []
    for p in ordered:
        entries.append(markdown_to_entry(p.read_text(encoding="utf-8"),
                                         source=str(p.relative_to(ENTRIES_DIR))))
    return entries


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_export(only_id: str = "") -> None:
    _, entries = load_kb()
    targets = [e for e in entries if not only_id or e.get("id") == only_id]
    if only_id and not targets:
        sys.exit(f"No entry with id '{only_id}'")

    written = 0
    for e in targets:
        p = entry_path(e)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(entry_to_markdown(e), encoding="utf-8")
        written += 1

    if not only_id:
        ENTRIES_DIR.mkdir(parents=True, exist_ok=True)
        INDEX_FILE.write_text(
            "# Entry order, mirroring coverage_kb.json. Rebuild reads this.\n"
            "# Delete a line to drop that entry from the corpus on --rebuild.\n"
            + "\n".join(str(entry_path(e).relative_to(ENTRIES_DIR)) for e in entries)
            + "\n",
            encoding="utf-8")

    by_cat: Dict[str, int] = {}
    for e in targets:
        by_cat[e.get("category", "?")] = by_cat.get(e.get("category", "?"), 0) + 1
    print(f"Exported {written} entr{'y' if written == 1 else 'ies'} to {ENTRIES_DIR}/")
    for cat, n in sorted(by_cat.items()):
        print(f"  {cat:16} {n:3}")
    print(f"\nThe JSON is unchanged and is still what the pipeline reads.")
    print(f"Edit the .md files, then: python kb_files.py --rebuild")


def _diff(json_entries, file_entries) -> List[str]:
    problems = []
    jmap = {e.get("id"): e for e in json_entries}
    fmap = {e.get("id"): e for e in file_entries}

    for missing in sorted(set(jmap) - set(fmap)):
        problems.append(f"in JSON but not in files: {missing}")
    for extra in sorted(set(fmap) - set(jmap)):
        problems.append(f"in files but not in JSON: {extra}  (would be ADDED)")

    for eid in sorted(set(jmap) & set(fmap)):
        for field in sorted(set(jmap[eid]) | set(fmap[eid])):
            a, b = jmap[eid].get(field), fmap[eid].get(field)
            if a != b:
                problems.append(f"{eid}: field '{field}' differs")
    return problems


def cmd_check() -> None:
    _, json_entries = load_kb()
    file_entries = read_files()
    problems = _diff(json_entries, file_entries)
    print(f"JSON: {len(json_entries)} entries    files: {len(file_entries)} entries")
    if not problems:
        print("In sync -- the files and the JSON say exactly the same thing.")
        return
    print(f"\n{len(problems)} difference(s):")
    for p in problems[:60]:
        print(f"  {p}")
    if len(problems) > 60:
        print(f"  ... and {len(problems) - 60} more")
    print("\n--rebuild would make the JSON match the files.")


def cmd_rebuild(force: bool) -> None:
    wrapper, json_entries = load_kb()
    file_entries = read_files()
    problems = _diff(json_entries, file_entries)

    if not problems:
        print("Files and JSON already agree -- nothing to write.")
        return

    print(f"{len(problems)} change(s) will be written into {config.KB_JSON}:")
    for p in problems[:40]:
        print(f"  {p}")
    if len(problems) > 40:
        print(f"  ... and {len(problems) - 40} more")

    if not force:
        reply = input("\nWrite these into the JSON? [y/N] ").strip().lower()
        if reply not in ("y", "yes"):
            print("Cancelled. Nothing was written.")
            return

    src = Path(config.KB_JSON)
    backup = src.with_suffix(f".bak-{datetime.now():%Y%m%d_%H%M%S}.json")
    shutil.copy2(src, backup)

    wrapper["entries"] = file_entries
    if isinstance(wrapper.get("metadata"), dict):
        wrapper["metadata"]["entry_count"] = len(file_entries)
        wrapper["metadata"]["last_rebuilt_from_files"] = datetime.now().isoformat(timespec="seconds")

    src.write_text(json.dumps(wrapper, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {len(file_entries)} entries to {src}")
    print(f"Previous version saved as {backup}")
    print("Sanity check the corpus now:  python kb_validate.py")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Explode the coverage knowledge base into one file per design, and back.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="The JSON is the source of truth. Only --rebuild writes it, and it backs it up first.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--export", action="store_true", help="JSON -> one .md per entry (default)")
    g.add_argument("--check", action="store_true", help="report where files and JSON differ; writes nothing")
    g.add_argument("--rebuild", action="store_true", help="files -> JSON (backs up the old JSON first)")
    ap.add_argument("--id", default="", help="operate on a single entry id")
    ap.add_argument("--yes", action="store_true", help="skip the confirmation prompt on --rebuild")
    args = ap.parse_args()

    if args.check:
        cmd_check()
    elif args.rebuild:
        cmd_rebuild(force=args.yes)
    else:
        cmd_export(only_id=args.id)


if __name__ == "__main__":
    main()
