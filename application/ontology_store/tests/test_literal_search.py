from .conftest import PYTHON


def labels(hits):
    return [h["label"] for h in hits]


def test_exact_label_comes_first(store):
    hits = store.literal_search("data scientist")
    assert hits[0]["label"] == "data scientist"


def test_match_is_case_insensitive(store):
    hits = store.literal_search("PYTHON")
    assert hits[0]["uri"] == PYTHON


def test_substring_in_description_matches(store):
    assert labels(store.literal_search("querytaal")) == ["SQL gebruiken"]


def test_label_matches_rank_above_description_matches(store):
    hits = labels(store.literal_search("data"))
    assert hits[:3] == ["data engineer", "data scientist", "data analyseren"]
    assert "machine learning toepassen" in hits[3:]


def test_filters_are_applied(store):
    hits = store.literal_search("data", {"class": "occupation"})
    assert {h["class"] for h in hits} == {"occupation"}
    assert len(hits) == 2


def test_limit(store):
    assert len(store.literal_search("e", limit=4)) == 4


def test_like_wildcards_are_escaped(store):
    assert store.literal_search("%") == []
    assert store.literal_search("_") == []


def test_empty_query_returns_nothing(store):
    assert store.literal_search("   ") == []
