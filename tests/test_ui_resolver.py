from am_normalizer.ui_resolver import resolve_ui_key  # type: ignore  # noqa: E402


def test_resolve_login_variants():
    # Latin input in your convention: ygbu (not yigbu)
    item = resolve_ui_key("ygbu")
    assert item is not None
    assert item["key"] == "ui.auth.login"
    assert item["am"] == "ይግቡ"

    # Ethiopic should resolve too
    item = resolve_ui_key("ይግቡ")
    assert item is not None
    assert item["key"] == "ui.auth.login"
