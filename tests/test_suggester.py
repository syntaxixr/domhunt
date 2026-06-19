from domhunt.suggester import variations


def test_returns_unique_candidates():
    out = variations("acme", limit=20)
    assert len(out) == len(set(out))
    assert "acme" not in out


def test_includes_natural_forms():
    out = variations("acme", limit=24)
    assert "acmeapp" in out
    assert "acmehq" in out
    assert "getacme" in out
    assert "tryacme" in out


def test_respects_limit():
    assert len(variations("foo", limit=5)) == 5
    assert len(variations("foo", limit=100)) <= 100


def test_handles_empty_and_edge():
    assert variations("") == []
    assert variations("---") == []
    assert "acme" not in variations("acme")


def test_strips_hyphens_in_output():
    for candidate in variations("acme", limit=30):
        assert not candidate.startswith("-")
        assert not candidate.endswith("-")
