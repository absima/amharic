
from am_normalizer.ui_resolver import resolve_ui_key  # type: ignore  # noqa: E402


def test_alias_resolves_login():
    item = resolve_ui_key("login")
    assert item is not None
    assert item["key"] == "ui.auth.login"
    assert item["am"] == "ይግቡ"


def test_alias_is_case_and_space_insensitive():
    item = resolve_ui_key("  LoGiN   ")
    assert item is not None
    assert item["key"] == "ui.auth.login"


def test_alias_resolves_yigbu_even_if_normalizer_wouldnt():
    item = resolve_ui_key("ygbu")
    assert item is not None
    assert item["key"] == "ui.auth.login"
