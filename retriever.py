#!/usr/bin/env python3
"""
retriever.py -- FAISS semantic retrieval over the coverage knowledge base.

This is the "Find Best Match (FAISS)" box of the architecture diagram. It
mirrors the retrieval design of the reference Assergent SVA project:

  * one embedding per entry, built from
        english_requirement + design type + signal names
  * sentence-transformers 'all-MiniLM-L6-v2' encoder
  * FAISS IndexFlatIP over L2-normalised vectors  ==  cosine similarity
  * top-k retrieval gated by a minimum-similarity threshold (tau), so a weak
    match is dropped rather than injected into the prompt as a bad example

The corpus is a SINGLE JSON file (knowledge_base/coverage_kb.json), not one
file per entry. Schema of each element of "entries":

    {
      "id":                  "mux2_1bit_001",
      "english_requirement": "Cover 2-to-1 multiplexer behavior ...",
      "coverage_model":      "covergroup cg_mux2 (ref logic a, b, sel) ... endgroup",
      "rtl":                 "module mux2(a, b, sel, y); ... endmodule",
      "design_context":      {"module": "MUX2", "data_width": 1,
                              "type": "2-to-1 multiplexer"},
      "signals":             ["a", "b", "sel", "y"],
      "verified":            true,
      "provenance":          "curated_seed" | "hand_authored" | "auto",
      "category":            "combinational" | "sequential" | ...,
      "notes":               "free-form"
    }

Two fields govern what may be retrieved, and the distinction matters:

  verified    the coverage model compiled and produced coverage in a REAL
              irun/IMC run. Nothing sets this on inspection alone.
  provenance  where the entry came from. "auto" entries are LLM output
              recorded by main.py and are withheld until verified; human
              "curated_seed"/"hand_authored" entries are retrievable once
              they pass kb_validate.py.

Admitting unverified LLM output would let a covergroup that never compiled be
retrieved later as a "successful example", and its errors imitated rather than
fixed -- a failure this pipeline hit in practice.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

import config

log = logging.getLogger("RAG-KB")

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


@dataclass
class CoverageEntry:
    entry_id: str
    english_requirement: str
    coverage_model: str
    rtl: str
    design_context: Dict
    signals: List[str]
    verified: bool = True
    notes: str = ""
    provenance: str = "hand_authored"
    category: str = ""
    embedding: Optional[np.ndarray] = field(default=None, repr=False)

    def retrievable(self) -> bool:
        """An entry may be retrieved if a real tool run proved it compiles, or
        if a human wrote it deliberately. LLM output recorded automatically
        (provenance "auto") must clear the compile bar first -- that is the
        guard against imitating a covergroup that never worked."""
        return self.verified or self.provenance in config.RAG_ALLOWED_PROVENANCE

    @property
    def module(self) -> str:
        return self.design_context.get("module", "")

    @property
    def design_type(self) -> str:
        return self.design_context.get("type", "")

    @property
    def data_width(self):
        return self.design_context.get("data_width", "")

    def search_text(self) -> str:
        """Text that gets embedded. Combines the natural-language requirement
        with the structural hints (design type, signal names) so retrieval
        keys on both what the coverage should do and what kind of block it
        runs against -- the same combination Assergent embeds."""
        return (f"{self.english_requirement} "
                f"{self.design_type} {self.module} "
                f"{' '.join(self.signals)}")

    def to_dict(self) -> Dict:
        return {
            "id": self.entry_id,
            "english_requirement": self.english_requirement,
            "coverage_model": self.coverage_model,
            "rtl": self.rtl,
            "design_context": self.design_context,
            "signals": self.signals,
            "verified": self.verified,
            "provenance": self.provenance,
            "category": self.category,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "CoverageEntry":
        return cls(
            entry_id=d["id"],
            english_requirement=d.get("english_requirement", ""),
            coverage_model=d.get("coverage_model", ""),
            rtl=d.get("rtl", ""),
            design_context=d.get("design_context", {}) or {},
            signals=d.get("signals", []) or [],
            verified=bool(d.get("verified", True)),
            notes=d.get("notes", ""),
            provenance=d.get("provenance", "hand_authored"),
            category=d.get("category", ""),
        )


class CoverageKnowledgeBase:
    """FAISS-backed semantic search over coverage_kb.json."""

    def __init__(self, db_path: str = None, retrievable_only: bool = True):
        self.db_path = Path(db_path or config.KB_JSON)
        self.retrievable_only = retrievable_only
        self.entries: List[CoverageEntry] = []      # indexed (retrievable) subset
        self.all_entries: List[CoverageEntry] = []  # everything on disk
        self.index = None
        self._encoder = None

        self._load()
        self._build_index()

    # Lazy so a run that never retrieves does not pay the model load cost.
    @property
    def encoder(self):
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer
            log.info(f"Loading embedding model '{config.EMBEDDING_MODEL}' ...")
            self._encoder = SentenceTransformer(config.EMBEDDING_MODEL)
        return self._encoder

    # ------------------------------------------------------------------ load

    def _load(self):
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            log.warning(f"Knowledge base not found at {self.db_path} -- starting empty. "
                        f"Seed it with `python kb_tool.py --seed` or add entries manually.")
            return

        data = json.loads(self.db_path.read_text(encoding="utf-8"))
        self.all_entries = [CoverageEntry.from_dict(d) for d in data.get("entries", [])]
        self.entries = ([e for e in self.all_entries if e.retrievable()]
                        if self.retrievable_only else list(self.all_entries))

        skipped = len(self.all_entries) - len(self.entries)
        log.info(f"Loaded {len(self.entries)} retrievable entries from {self.db_path}"
                 + (f" ({skipped} withheld pending a successful compile)" if skipped else ""))

    def _build_index(self):
        if not self.entries:
            self.index = None
            return

        import faiss

        vectors = self._embed([e.search_text() for e in self.entries])
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)

        for e, v in zip(self.entries, vectors):
            e.embedding = v

        log.info(f"Built FAISS index with {self.index.ntotal} entries")

    def _embed(self, texts: List[str]) -> np.ndarray:
        """Encode and L2-normalise, so inner product == cosine similarity."""
        vecs = self.encoder.encode(texts, show_progress_bar=False)
        vecs = np.asarray(vecs, dtype="float32")
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return (vecs / norms).astype("float32")

    # -------------------------------------------------------------- retrieve

    def retrieve(self, query: str, k: int = None,
                 min_similarity: float = None) -> List[Tuple[CoverageEntry, float]]:
        """Top-k entries above the confidence gate, best first."""
        if not self.entries or self.index is None or not query.strip():
            return []

        k = k or config.RAG_TOP_K
        tau = config.RAG_MIN_SIMILARITY if min_similarity is None else min_similarity

        sims, idxs = self.index.search(self._embed([query]), min(k, len(self.entries)))

        results = [(self.entries[i], float(s))
                   for s, i in zip(sims[0], idxs[0])
                   if i >= 0 and s >= tau]

        if results:
            log.info(f"Retrieved {len(results)} entries above tau={tau}")
            for n, (e, s) in enumerate(results, 1):
                log.info(f"  {n}. {e.entry_id} ({e.design_type}) similarity={s:.3f}")
        else:
            best = float(sims[0][0]) if len(sims[0]) else 0.0
            log.info(f"No entry cleared tau={tau} (best was {best:.3f}) -- "
                     f"generating without precedent")
        return results

    # ------------------------------------------------------------------- add

    def add_entry(self, english_requirement: str, coverage_model: str, rtl: str,
                  design_context: Dict, signals: List[str],
                  verified: bool = False, notes: str = "",
                  entry_id: str = None, provenance: str = "auto") -> CoverageEntry:
        """Append an entry and persist. Defaults to verified=False so a newly
        generated model is recorded but NOT retrievable until something proves
        it compiles (see kb_tool.py --verify / main.py's post-simulation hook).
        """
        module = (design_context or {}).get("module", "design")
        entry_id = entry_id or f"{module.lower()}_{int(time.time())}"

        entry = CoverageEntry(
            entry_id=entry_id, english_requirement=english_requirement,
            coverage_model=coverage_model, rtl=rtl,
            design_context=design_context or {}, signals=signals or [],
            verified=verified, notes=notes, provenance=provenance,
        )

        self.all_entries.append(entry)
        if entry.retrievable() or not self.retrievable_only:
            vec = self._embed([entry.search_text()])
            if self.index is None:
                import faiss
                self.index = faiss.IndexFlatIP(vec.shape[1])
            self.index.add(vec)
            entry.embedding = vec[0]
            self.entries.append(entry)

        self._persist()
        log.info(f"Added entry {entry_id} (verified={verified}); "
                 f"corpus={len(self.all_entries)}, indexed={len(self.entries)}")
        return entry

    def mark_verified(self, entry_id: str) -> bool:
        for e in self.all_entries:
            if e.entry_id == entry_id:
                e.verified = True
                self._persist()
                log.info(f"Marked {entry_id} verified")
                return True
        return False

    def _persist(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "metadata": {
                "schema_version": "1.0",
                "description": ("Retrieval corpus for coverage-model generation: "
                                "(English requirement, RTL, golden coverage model) triples."),
                "total_entries": len(self.all_entries),
                "verified_entries": sum(1 for e in self.all_entries if e.verified),
            },
            "entries": [e.to_dict() for e in self.all_entries],
        }
        self.db_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


_kb: Optional[CoverageKnowledgeBase] = None


def get_kb() -> CoverageKnowledgeBase:
    """Singleton so prompt_builder and main.py share one encoder + index."""
    global _kb
    if _kb is None:
        _kb = CoverageKnowledgeBase()
    return _kb
