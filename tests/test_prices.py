from domhunt.prices import porkbun_url, price_for


def test_known_tlds_have_prices():
    for tld in ("com", "io", "dev", "app", "ai"):
        assert price_for(tld) is not None
        assert price_for(tld) > 0


def test_unknown_tld_returns_none():
    assert price_for("nope-not-real") is None


def test_normalises_input():
    assert price_for(".com") == price_for("com") == price_for("COM")


def test_porkbun_url_format():
    assert porkbun_url("acme.dev") == "https://porkbun.com/checkout/search?q=acme.dev"
