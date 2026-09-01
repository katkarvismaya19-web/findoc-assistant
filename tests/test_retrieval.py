"""Unit tests that run without a built index or an API key.

Covers the pure logic: text cleaning, chunk construction, tokenization, and
the fusion maths. The parts that need embeddings are exercised by the
evaluation harness instead.
"""
import pytest

from app.text import build_chunks, clean, reciprocal_rank_fusion, tokenize


def test_clean_collapses_whitespace():
    assert clean("a  \t b\n\n\n\nc") == "a b\n\nc"


def test_clean_strips_null_bytes():
    assert "\x00" not in clean("bad\x00text")


def test_build_chunks_preserves_provenance():
    pages = [{"source": "circular.pdf", "page": 7, "text": "word " * 400}]
    chunks = build_chunks(pages, chunk_size=200, overlap=20)
    assert len(chunks) > 1
    assert all(c["source"] == "circular.pdf" for c in chunks)
    assert all(c["page"] == 7 for c in chunks)
    assert len(set(c["id"] for c in chunks)) == len(chunks), "ids must be unique"


def test_build_chunks_drops_tiny_fragments():
    pages = [{"source": "x.pdf", "page": 1, "text": "hi"}]
    assert build_chunks(pages, chunk_size=500, overlap=50) == []


def test_tokenize_lowercases_and_keeps_alphanumerics():
    assert tokenize("DOR.AUT.REC-12/2023") == ["dor", "aut", "rec", "12", "2023"]


def test_tokenize_drops_punctuation_only_input():
    assert tokenize("!!! ,. ---") == []


def rrf(ranked_lists, k=60):
    scores = reciprocal_rank_fusion(ranked_lists, k)
    return sorted(scores, key=scores.get, reverse=True)


def test_rrf_rewards_agreement_between_rankers():
    dense = ["a", "b", "c"]
    lexical = ["c", "b", "d"]
    # b is ranked 2nd by both; c is 3rd and 1st. Both beat single-list-only docs.
    assert set(rrf([dense, lexical])[:2]) == {"b", "c"}
    assert rrf([dense, lexical])[-1] == "d"


def test_rrf_ties_produce_equal_scores():
    # Ranked 1st and 2nd by opposite lists, x and y must score identically.
    # Their final order is then arbitrary, so assert on scores, not sequence.
    scores = reciprocal_rank_fusion([["x", "y"], ["y", "x"]])
    assert scores["x"] == pytest.approx(scores["y"])


@pytest.mark.parametrize("size,overlap", [(500, 75), (1000, 150)])
def test_chunk_sizes_both_produce_output(size, overlap):
    pages = [{"source": "d.pdf", "page": 1, "text": "sentence here. " * 300}]
    assert len(build_chunks(pages, size, overlap)) > 0
