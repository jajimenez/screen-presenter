from PySide6.QtCore import QCameraPermission, QCoreApplication, QObject, Qt, Signal
from PySide6.QtMultimedia import (
    QCamera,
    QCameraDevice,
    QMediaCaptureSession,
    QMediaDevices,
)

CAMERA_ACCESS_DENIED_MESSAGE = (
    "Camera access denied. Check that this application has camera access in the system "
    "privacy settings."
)


def _application() -> QCoreApplication:
    """Return the running application, which must exist before cameras are used."""
    app = QCoreApplication.instance()
    assert app is not None

    return app


class CameraController(QObject):
    """Discovers cameras and routes the selected one to a capture session."""

    # Camera descriptions and the index that should be shown as selected
    cameras_changed = Signal(list, int)

    # Error text to display; an empty string means there is no error
    error_changed = Signal(str)

    # Emitted after the user answers the system permission prompt
    permission_answered = Signal()

    def __init__(
        self,
        capture_session: QMediaCaptureSession,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._capture_session = capture_session
        self._cameras: list[QCameraDevice] = []
        self._camera: QCamera | None = None
        # Camera waiting for permission; its QCamera is only created once access is
        # granted, as Qt logs a warning when a QCamera is created without access
        self._pending_camera: QCameraDevice | None = None

        # Update the list when cameras are added or removed
        self._media_devices = QMediaDevices(self)
        self._media_devices.videoInputsChanged.connect(self.update)

    def update(self) -> None:
        """Update the list of cameras, keeping the current one if it is still there."""
        current_id = self._camera.cameraDevice().id() if self._camera else None
        self._cameras = QMediaDevices.videoInputs()
        index = next(
            (i for i, c in enumerate(self._cameras) if c.id() == current_id),
            None,
        )

        self.cameras_changed.emit([c.description() for c in self._cameras], index or 0)

        # Only switch cameras when the current one is gone, to avoid restarting it
        if index is None:
            self.select(0)

    def select(self, index: int) -> None:
        """Select the camera at the given index."""
        self.error_changed.emit("")
        self._release_camera()

        if not 0 <= index < len(self._cameras):
            return

        self._pending_camera = self._cameras[index]
        self._start_camera()

    def _release_camera(self) -> None:
        """Stop and release the current camera."""
        self._pending_camera = None

        if self._camera is None:
            return

        self._camera.stop()
        # The PySide6 stub omits None, which Qt accepts to detach the camera
        self._capture_session.setCamera(None)  # pyright: ignore[reportArgumentType]
        self._camera.deleteLater()
        self._camera = None

    def _start_camera(self) -> None:
        """Start the camera, asking for permission first if needed."""
        permission = QCameraPermission()
        status = self._permission_status()

        if status == Qt.PermissionStatus.Undetermined:
            _application().requestPermission(
                permission, self, self._on_permission_result
            )
        else:
            self._apply_permission(status)

    def _on_permission_result(self) -> None:
        """Continue once the user has answered the permission prompt."""
        self._apply_permission(self._permission_status())
        self.permission_answered.emit()

    def _apply_permission(self, status: Qt.PermissionStatus) -> None:
        """Start the camera if access is granted, or report that it is denied."""
        if status == Qt.PermissionStatus.Granted:
            if self._pending_camera is not None:
                self._camera = QCamera(self._pending_camera, self)
                self._pending_camera = None
                self._camera.errorOccurred.connect(self._on_camera_error)
                self._capture_session.setCamera(self._camera)
                self._camera.start()
        elif status == Qt.PermissionStatus.Denied:
            self.error_changed.emit(CAMERA_ACCESS_DENIED_MESSAGE)

    def _permission_status(self) -> Qt.PermissionStatus:
        """Return the current camera permission status."""
        return _application().checkPermission(QCameraPermission())

    def _on_camera_error(self, error: QCamera.Error, error_text: str) -> None:
        """Report an error encountered by the camera."""
        self.error_changed.emit(error_text)
