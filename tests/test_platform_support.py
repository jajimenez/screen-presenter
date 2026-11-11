import pytest

from screen_presenter import platform_support


@pytest.mark.parametrize(
    ("platform", "expected_name"),
    [("darwin", "logo-macos.svg"), ("win32", "logo.svg"), ("linux", "logo.svg")],
)
def test_get_logo_path_depends_on_platform(
    monkeypatch: pytest.MonkeyPatch, platform: str, expected_name: str
) -> None:
    monkeypatch.setattr(platform_support.sys, "platform", platform)

    assert platform_support.get_logo_path() == (
        platform_support.RESOURCES_PATH / expected_name
    )


def test_set_up_platform_sets_windows_app_id(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(platform_support.sys, "platform", "win32")
    monkeypatch.setattr(platform_support, "_set_windows_app_id", calls.append)
    monkeypatch.setattr(
        platform_support,
        "_set_camera_usage_description",
        lambda: pytest.fail("MacOS setup must not run on Windows"),
    )

    platform_support.set_up_platform("io.example.app")

    assert calls == ["io.example.app"]


def test_set_up_platform_sets_camera_usage_description_on_macos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(platform_support.sys, "platform", "darwin")
    monkeypatch.setattr(
        platform_support, "_set_windows_app_id", lambda app_id: calls.append(app_id)
    )
    monkeypatch.setattr(
        platform_support,
        "_set_camera_usage_description",
        lambda: calls.append("camera"),
    )

    platform_support.set_up_platform("io.example.app")

    assert calls == ["camera"]


def test_set_up_platform_does_nothing_on_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platform_support.sys, "platform", "linux")
    monkeypatch.setattr(
        platform_support,
        "_set_windows_app_id",
        lambda app_id: pytest.fail("Windows setup must not run on Linux"),
    )
    monkeypatch.setattr(
        platform_support,
        "_set_camera_usage_description",
        lambda: pytest.fail("MacOS setup must not run on Linux"),
    )

    platform_support.set_up_platform("io.example.app")
