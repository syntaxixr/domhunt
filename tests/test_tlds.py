from domhunt.tlds import DEFAULT_TLDS, EXTENDED_TLDS, resolve_tlds


def test_default_when_none():
    assert resolve_tlds(None) == list(DEFAULT_TLDS)


def test_all_keyword():
    assert resolve_tlds("all") == list(EXTENDED_TLDS)
    assert resolve_tlds("ALL") == list(EXTENDED_TLDS)


def test_custom_list_normalizes():
    assert resolve_tlds("COM, .io,Dev") == ["com", "io", "dev"]


def test_skips_blanks():
    assert resolve_tlds("com,, io , ") == ["com", "io"]
