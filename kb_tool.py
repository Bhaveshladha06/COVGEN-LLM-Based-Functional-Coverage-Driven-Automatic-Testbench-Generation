#!/usr/bin/env python3
"""
kb_tool.py -- inspect and curate the coverage knowledge base.

The corpus lives in one JSON file (knowledge_base/coverage_kb.json). This tool
avoids hand-editing it, which is easy to get wrong once coverage models contain
braces, quotes and newlines.

    python kb_tool.py --list
    python kb_tool.py --show mux2_1bit_001
    python kb_tool.py --query "cover a counter wrapping from max to zero"
    python kb_tool.py --add --rtl designs/fifo/fifo.v \\
                      --spec designs/fifo/fifo.spec.txt \\
                      --model designs/fifo/fifo_coverage.sv \\
                      --type "synchronous FIFO" --verified
    python kb_tool.py --verify fifo_1234567890
    python kb_tool.py --stats
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import config


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8").strip()


def cmd_list(kb):
    if not kb.all_entries:
        print("Knowledge base is empty.")
        return
    print(f"{'ID':<28} {'VERIFIED':<9} {'TYPE':<26} SIGNALS")
    print("-" * 92)
    for e in kb.all_entries:
        flag = "yes" if e.verified else "NO"
        print(f"{e.entry_id:<28} {flag:<9} {e.design_type[:25]:<26} {', '.join(e.signals)}")
    print(f"\n{len(kb.all_entries)} entries, {sum(1 for e in kb.all_entries if e.verified)} verified "
          f"({len(kb.entries)} indexed for retrieval)")


def cmd_show(kb, entry_id):
    for e in kb.all_entries:
        if e.entry_id == entry_id:
            print(json.dumps(e.to_dict(), indent=2))
            return 0
    print(f"No entry with id '{entry_id}'", file=sys.stderr)
    return 1


def cmd_query(kb, text, k, tau):
    results = kb.retrieve(text, k=k, min_similarity=tau)
    if not results:
        print(f"Nothing cleared the similarity threshold ({tau}).")
        print("This is expected on a small corpus -- generation falls back to rules only.")
        return
    print(f"\nTop {len(results)} matches for: {text!r}\n")
    for i, (e, s) in enumerate(results, 1):
        print(f"{i}. {e.entry_id}   similarity={s:.3f}")
        print(f"   type   : {e.design_type}")
        print(f"   signals: {', '.join(e.signals)}")
        print(f"   req    : {e.english_requirement[:100]}...")
        print()


def cmd_for_design(kb, rtl_path, k, tau, show_prompt):
    """Show what retrieval would return for a real design, without calling any
    LLM. This is the cheap way to tune tau and judge corpus coverage."""
    import prompt_builder as pb

    design = pb.parse_design(rtl_path)
    query = pb._retrieval_query(design)

    print(f"\nDesign      : {design.name}   ({rtl_path})")
    print(f"Ports       : {', '.join(p['name'] for p in design.ports)}")
    print(f"Clocking    : {'sequential, clock=' + design.clock if design.clock else 'combinational'}")
    print(f"Spec loaded : {'yes' if design.coverage_spec else 'NO (.spec.txt missing)'}")
    print(f"\nEmbedded query:\n  {query[:300]}")

    # Score every entry so near-misses below tau are visible, not just winners.
    scored = kb.retrieve(query, k=len(kb.entries) or 1, min_similarity=-1.0)
    if not scored:
        print("\nCorpus is empty -- nothing to retrieve.")
        return

    print(f"\nAll {len(scored)} entries by similarity (tau = {tau}):")
    print(f"  {'SCORE':<8} {'':<4} {'ID':<26} TYPE")
    print("  " + "-" * 72)
    for entry, score in scored:
        mark = "USED" if score >= tau else "  --"
        print(f"  {score:<8.3f} {mark:<4} {entry.entry_id:<26} {entry.design_type}")

    used = [(e, s) for e, s in scored if s >= tau][:k]
    print(f"\n=> {len(used)} example(s) would be injected into the prompt "
          f"(top-k = {k}).")
    if not used:
        best = scored[0][1]
        print(f"   Best was {best:.3f}, short of tau={tau}. The model would generate "
              f"from rules only.\n   Lower RAG_MIN_SIMILARITY in config.py, or seed a "
              f"closer example, to change this.")

    if show_prompt:
        print("\n" + "=" * 72)
        print("FULL PROMPT THAT WOULD BE SENT")
        print("=" * 72)
        print(pb.build_coverage_model_prompt(design))


def cmd_add(kb, args):
    rtl = _read(args.rtl)
    model = _read(args.model)
    spec = _read(args.spec) if args.spec else args.requirement
    if not spec:
        print("Provide --spec <file> or --requirement <text>", file=sys.stderr)
        return 1

    import re
    m = re.search(r'\bmodule\s+(\w+)', rtl)
    module = (m.group(1) if m else Path(args.rtl).stem).upper()

    signals = args.signals.split(",") if args.signals else _infer_signals(rtl)

    entry = kb.add_entry(
        english_requirement=spec,
        coverage_model=model,
        rtl=rtl,
        design_context={"module": module,
                        "data_width": args.data_width,
                        "type": args.type or "unspecified"},
        signals=[s.strip() for s in signals if s.strip()],
        verified=args.verified,
        notes=args.notes or "",
    )
    print(f"Added {entry.entry_id} (verified={entry.verified})")
    if not entry.verified:
        print("NOT retrievable until verified. Once its coverage model compiles and "
              f"produces coverage, run:\n  python kb_tool.py --verify {entry.entry_id}")
    return 0


def _infer_signals(rtl: str):
    import re
    pat = re.compile(r'\b(?:input|output|inout)\s+(?:wire\s+|reg\s+|logic\s+)?'
                     r'(?:signed\s+)?(?:\[[^\]]+\]\s*)?(\w+)')
    seen, out = set(), []
    for name in pat.findall(rtl):
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def cmd_stats(kb):
    total = len(kb.all_entries)
    ver = sum(1 for e in kb.all_entries if e.verified)
    print(f"Corpus file      : {kb.db_path}")
    print(f"Total entries    : {total}")
    print(f"Verified         : {ver}")
    print(f"Indexed (usable) : {len(kb.entries)}")
    print(f"Embedding model  : {config.EMBEDDING_MODEL}")
    print(f"Top-k / tau      : {config.RAG_TOP_K} / {config.RAG_MIN_SIMILARITY}")
    if total:
        print("\nBy design type:")
        counts = {}
        for e in kb.all_entries:
            counts[e.design_type] = counts.get(e.design_type, 0) + 1
        for t, n in sorted(counts.items(), key=lambda kv: -kv[1]):
            print(f"  {n:>3}  {t}")


def main():
    p = argparse.ArgumentParser(description="Inspect and curate the coverage knowledge base")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true")
    g.add_argument("--show", metavar="ID")
    g.add_argument("--query", metavar="TEXT")
    g.add_argument("--for-design", metavar="RTL", dest="for_design",
                   help="Parse an RTL file (plus its .spec.txt) and show exactly what "
                        "FAISS would retrieve for it. Makes no API calls.")
    g.add_argument("--add", action="store_true")
    g.add_argument("--verify", metavar="ID")
    g.add_argument("--stats", action="store_true")

    p.add_argument("--rtl"), p.add_argument("--model"), p.add_argument("--spec")
    p.add_argument("--requirement"), p.add_argument("--type"), p.add_argument("--signals")
    p.add_argument("--notes")
    p.add_argument("--data-width", type=int, default=1, dest="data_width")
    p.add_argument("--verified", action="store_true",
                   help="Mark the new entry retrievable immediately. Only pass this if the "
                        "coverage model has actually compiled.")
    p.add_argument("-k", type=int, default=None)
    p.add_argument("--tau", type=float, default=None)
    p.add_argument("--show-prompt", action="store_true", dest="show_prompt",
                   help="With --for-design, also print the full prompt that would be sent.")
    args = p.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    from retriever import CoverageKnowledgeBase
    # retrievable_only=False so curation commands see withheld entries too.
    kb = CoverageKnowledgeBase(retrievable_only=False)

    if args.list:
        cmd_list(kb)
    elif args.show:
        return cmd_show(kb, args.show)
    elif args.query:
        cmd_query(kb, args.query, args.k or config.RAG_TOP_K,
                  args.tau if args.tau is not None else config.RAG_MIN_SIMILARITY)
    elif args.for_design:
        cmd_for_design(kb, args.for_design, args.k or config.RAG_TOP_K,
                       args.tau if args.tau is not None else config.RAG_MIN_SIMILARITY,
                       args.show_prompt)
    elif args.add:
        if not (args.rtl and args.model):
            print("--add needs --rtl and --model", file=sys.stderr)
            return 1
        return cmd_add(kb, args)
    elif args.verify:
        if kb.mark_verified(args.verify):
            print(f"{args.verify} is now verified and retrievable.")
        else:
            print(f"No entry with id '{args.verify}'", file=sys.stderr)
            return 1
    elif args.stats:
        cmd_stats(kb)
    return 0


if __name__ == "__main__":
    sys.exit(main())
