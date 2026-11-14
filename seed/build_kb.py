#!/usr/bin/env python3
"""
build_kb.py -- assemble knowledge_base/coverage_kb.json from the seed modules.

Run from the project root:
    python seed/build_kb.py            # rebuild the corpus
    python seed/build_kb.py --dry-run  # report what would be written

Provenance is recorded honestly per entry:

  curated_seed  -- supplied with the project (the original six examples)
  hand_authored -- written for the corpus and checked by kb_validate.py, but
                   NOT yet compiled by a real tool
  auto          -- recorded by main.py from an actual pipeline run

`verified` means one thing only: the coverage model compiled and produced
coverage in a real irun/IMC run. Nothing here sets verified=True on the basis
of inspection alone -- that is what let broken models get retrieved as
"known-good examples" before.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "seed"))

import config  # noqa: E402

import seed_combinational  # noqa: E402
import seed_sequential     # noqa: E402
import seed_memory         # noqa: E402
import seed_control        # noqa: E402
import seed_curated        # noqa: E402

MODULES = [
    ("combinational", seed_combinational),
    ("sequential", seed_sequential),
    ("memory", seed_memory),
    ("control", seed_control),
    ("curated", seed_curated),
]

# The six originally supplied with the project. Kept as curated_seed and left
# verified, since they came from the project's own reference material.
CURATED_IDS = {
    "mux2_1bit_001", "mux4_1bit_001", "full_adder_1bit_001",
    "adder8_8bit_001", "prio_enc_4bit_001", "decoder2to4_2bit_001",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default=str(ROOT / config.KB_JSON))
    args = ap.parse_args()

    out_path = Path(args.out)

    # Preserve anything already in the corpus that the seed modules do not define
    # (in particular auto-recorded entries from real runs).
    existing = {}
    if out_path.exists():
        for e in json.loads(out_path.read_text(encoding="utf-8")).get("entries", []):
            existing[e["id"]] = e

    entries, by_category, seen = [], {}, set()

    for category, mod in MODULES:
        for raw in mod.E:
            eid = raw["id"]
            if eid in seen:
                print(f"ERROR: duplicate id {eid}", file=sys.stderr)
                return 1
            seen.add(eid)

            prior = existing.get(eid, {})
            curated = eid in CURATED_IDS

            entries.append({
                "id": eid,
                "english_requirement": raw["english_requirement"],
                "coverage_model": raw["coverage_model"],
                "rtl": raw["rtl"],
                "design_context": raw["design_context"],
                "signals": raw["signals"],
                # Only a real tool run flips this. A previously verified entry
                # keeps its status across rebuilds.
                "verified": bool(prior.get("verified", curated)),
                "provenance": "curated_seed" if curated else "hand_authored",
                "category": category,
                "notes": prior.get("notes", ""),
            })
            by_category[category] = by_category.get(category, 0) + 1

    # Carry forward entries not defined by the seed modules: the originally
    # supplied examples, plus anything auto-recorded from a real run.
    carried = 0
    for eid, e in existing.items():
        if eid in seen:
            continue
        curated = eid in CURATED_IDS
        e.setdefault("provenance", "curated_seed" if curated else "auto")
        e.setdefault("category", "curated" if curated else "auto")
        entries.append(e)
        carried += 1

    db = {
        "metadata": {
            "schema_version": "1.1",
            "description": ("Retrieval corpus for coverage-model generation: "
                            "(english_requirement, rtl, coverage_model) triples."),
            "total_entries": len(entries),
            "verified_entries": sum(1 for e in entries if e.get("verified")),
            "by_category": by_category,
            "provenance_note": (
                "verified=true means the coverage model compiled and produced "
                "coverage in a real irun/IMC run. hand_authored entries have "
                "passed kb_validate.py structural checks only."),
        },
        "entries": entries,
    }

    print(f"Seed entries : {len(seen)}")
    for cat, n in by_category.items():
        print(f"  {n:>3}  {cat}")
    if carried:
        print(f"Carried over : {carried} auto-recorded entries")
    print(f"Total        : {len(entries)}")
    print(f"Verified     : {db['metadata']['verified_entries']}")

    if args.dry_run:
        print("\n(dry run -- nothing written)")
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(db, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
