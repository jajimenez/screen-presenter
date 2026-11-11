from collections.abc import Callable
from typing import Any

import pytest
from PySide6.QtCore import Qt

from screen_presenter import camera_controller
from screen_presenter.camera_controller import (
    CAMERA_ACCESS_DENIED_MESSAGE,
    CameraController,
)


class FakeSignal:
    """Records connected slots; stands in for a Qt signal in tests."""

    def __init__(self) -> None:
        self.slots: list[Callable[..., Any]] = []

    def connect(self, slot: Callable[..., Any]) -> None:
        self.slots.append(slot)


class FakeCameraDevice:
    def __init__(self, camera_id: str, description: str) -> None:
        self._id = camera_id
        self._description = description

    def id(self) -> str:
        return self._id

    def description(self) -> str:
        return self._description


class FakeCamera:
    def __init__(self, device: FakeCameraDevice, parent: Any = None) -> None:
        self.device = device
        self.started = False
        self.stopped = False
        self.deleted = False
        self.errorOccurred = FakeSignal()

    def cameraDevice(self) -> FakeCameraDevice:
        return self.device

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def deleteLater(self) -> None:
        self.deleted = True


class FakeCaptureSession:
    def __init__(self) -> None:
        self.camera: Any = None

    def setCamera(self, camera: Any) -> None:
        self.camera = camera


class FakeApplication:
    def __init__(self) -> None:
        self.permission_slot: Callable[[], None] | None = None

    def requestPermission(self, permission: Any, receiver: Any, slot: Any) -> None:
        self.permission_slot = slot


@pytest.fixture
def cameras(monkeypatch: pytest.MonkeyPatch) -> list[FakeCameraDevice]:
    """Replace Qt's camera discovery with a list the test can change."""
    available: list[FakeCameraDevice] = []

    class FakeMediaDevices:
        videoInputsChanged = FakeSignal()

        def __init__(self, parent: Any = None) -> None:
            pass

        @staticmethod
        def videoInputs() -> list[FakeCameraDevice]:
            return available

    monkeypatch.setattr(camera_controller, "QMediaDevices", FakeMediaDevices)
    monkeypatch.setattr(camera_controller, "QCamera", FakeCamera)

    return available


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> FakeApplication:
    fake_app = FakeApplication()
    monkeypatch.setattr(camera_controller, "_application", lambda: fake_app)

    return fake_app


@pytest.fixture
def session() -> FakeCaptureSession:
    return FakeCaptureSession()


@pytest.fixture
def controller(
    cameras: list[FakeCameraDevice], session: FakeCaptureSession
) -> CameraController:
    return CameraController(session)  # type: ignore[arg-type]


def record(signal: Any) -> list[tuple[Any, ...]]:
    """Collect the arguments of every emission of a Qt signal."""
    emitted: list[tuple[Any, ...]] = []
    signal.connect(lambda *args: emitted.append(args))

    return emitted


def grant(controller: CameraController, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        controller, "_permission_status", lambda: Qt.PermissionStatus.Granted
    )


def test_update_lists_cameras_and_selects_first_when_none_selected(
    controller: CameraController,
    cameras: list[FakeCameraDevice],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cameras.extend([FakeCameraDevice("a", "Front"), FakeCameraDevice("b", "Back")])
    selected: list[int] = []
    monkeypatch.setattr(controller, "select", selected.append)
    emitted = record(controller.cameras_changed)

    controller.update()

    assert emitted == [(["Front", "Back"], 0)]
    assert selected == [0]


def test_update_keeps_current_camera_when_still_present(
    controller: CameraController,
    cameras: list[FakeCameraDevice],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cameras.extend([FakeCameraDevice("a", "Front"), FakeCameraDevice("b", "Back")])
    controller._camera = FakeCamera(FakeCameraDevice("b", "Back"))  # type: ignore[assignment]
    selected: list[int] = []
    monkeypatch.setattr(controller, "select", selected.append)
    emitted = record(controller.cameras_changed)

    controller.update()

    assert emitted == [(["Front", "Back"], 1)]
    assert selected == []


def test_select_out_of_range_releases_camera_and_starts_nothing(
    controller: CameraController,
    cameras: list[FakeCameraDevice],
    session: FakeCaptureSession,
    monkeypatch: pytest.MonkeyPatch,
    app: FakeApplication,
) -> None:
    cameras.append(FakeCameraDevice("a", "Front"))
    controller._cameras = list(cameras)  # type: ignore[assignment]
    grant(controller, monkeypatch)
    controller.select(0)
    camera = controller._camera
    assert camera is not None

    controller.select(5)

    assert camera.stopped  # type: ignore[union-attr]
    assert camera.deleted  # type: ignore[union-attr]
    assert session.camera is None
    assert controller._camera is None


def test_select_with_granted_permission_starts_camera(
    controller: CameraController,
    cameras: list[FakeCameraDevice],
    session: FakeCaptureSession,
    monkeypatch: pytest.MonkeyPatch,
    app: FakeApplication,
) -> None:
    cameras.extend([FakeCameraDevice("a", "Front"), FakeCameraDevice("b", "Back")])
    controller._cameras = list(cameras)  # type: ignore[assignment]
    grant(controller, monkeypatch)
    available = record(controller.selected_camera_available_changed)

    controller.select(1)

    camera = controller._camera
    assert isinstance(camera, FakeCamera)
    assert camera.device.id() == "b"
    assert camera.started
    assert session.camera is camera
    assert available[-1] == (True,)


def test_select_with_denied_permission_reports_error(
    controller: CameraController,
    cameras: list[FakeCameraDevice],
    session: FakeCaptureSession,
    monkeypatch: pytest.MonkeyPatch,
    app: FakeApplication,
) -> None:
    cameras.append(FakeCameraDevice("a", "Front"))
    controller._cameras = list(cameras)  # type: ignore[assignment]
    monkeypatch.setattr(
        controller, "_permission_status", lambda: Qt.PermissionStatus.Denied
    )
    errors = record(controller.error_changed)

    controller.select(0)

    assert controller._camera is None
    assert session.camera is None
    assert errors[-1] == (CAMERA_ACCESS_DENIED_MESSAGE,)


def test_select_when_undetermined_waits_for_permission_answer(
    controller: CameraController,
    cameras: list[FakeCameraDevice],
    session: FakeCaptureSession,
    monkeypatch: pytest.MonkeyPatch,
    app: FakeApplication,
) -> None:
    cameras.append(FakeCameraDevice("a", "Front"))
    controller._cameras = list(cameras)  # type: ignore[assignment]
    monkeypatch.setattr(
        controller, "_permission_status", lambda: Qt.PermissionStatus.Undetermined
    )
    answered = record(controller.permission_answered)

    controller.select(0)

    # No camera is created until the user answers the prompt
    assert controller._camera is None
    assert app.permission_slot is not None

    grant(controller, monkeypatch)
    app.permission_slot()

    assert isinstance(controller._camera, FakeCamera)
    assert controller._camera.started
    assert session.camera is controller._camera
    assert answered == [()]


def test_select_emits_empty_error_to_clear_previous_error(
    controller: CameraController,
    cameras: list[FakeCameraDevice],
    monkeypatch: pytest.MonkeyPatch,
    app: FakeApplication,
) -> None:
    cameras.append(FakeCameraDevice("a", "Front"))
    controller._cameras = list(cameras)  # type: ignore[assignment]
    grant(controller, monkeypatch)
    errors = record(controller.error_changed)

    controller.select(0)

    assert errors[0] == ("",)
