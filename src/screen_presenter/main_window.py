from PySide6.QtCore import QCameraPermission, QSettings, Qt
from PySide6.QtGui import QCloseEvent, QKeyEvent, QMouseEvent
from PySide6.QtMultimedia import QCamera, QMediaCaptureSession, QMediaDevices
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

CAMERA_ACCESS_DENIED_MESSAGE = (
    "Camera access denied. Check that this application has camera access in the system "
    "privacy settings."
)

class MainWindow(QMainWindow):
    # Class defaults, since Qt events can run before __init__ assigns instance
    # attributes
    _presentation_mode = False
    _drag_offset = None

    def __init__(self, parent: QWidget | None = None):
        """Initialize the main window."""
        super().__init__(parent)

        # Window title and size
        self.setWindowTitle(QApplication.applicationDisplayName())
        self.setMinimumSize(150, 150)
        self.resize(400, 300)

        # Camera discovery
        self._media_devices = QMediaDevices(self)
        self._cameras = []
        self._camera = None
        self._presentation_mode = False
        self._drag_offset = None

        # Camera selector
        self._camera_combo = QComboBox()
        self._camera_combo.currentIndexChanged.connect(self._select_camera)

        # Button for entering presentation mode
        self._present_button = QPushButton("Present")
        self._present_button.clicked.connect(self._enter_presentation_mode)

        # Layout for the camera selector and present button
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.addWidget(self._camera_combo, 1)
        controls_layout.addWidget(self._present_button)

        # Container widget for the controls
        self._controls = QWidget()
        self._controls.setLayout(controls_layout)

        # Video widget for displaying the camera image
        self._video_widget = QVideoWidget()
        self._video_widget.setAspectRatioMode(
            Qt.AspectRatioMode.KeepAspectRatioByExpanding
        )

        # Message shown when the camera cannot be used, such as when access is denied
        self._message_label = QLabel()
        self._message_label.setWordWrap(True)
        self._message_label.hide()

        # Refresh the list when cameras are added or removed
        self._media_devices.videoInputsChanged.connect(self._update_cameras)

        # Capture pipeline: camera -> capture session -> video widget
        self._capture_session = QMediaCaptureSession(self)
        self._capture_session.setVideoOutput(self._video_widget)

        # Stack the selector above the video preview
        self._layout = QVBoxLayout()
        self._layout.addWidget(self._controls)
        self._layout.addWidget(self._message_label)
        self._layout.addWidget(self._video_widget, 1)

        # Attach the layout to the window
        central_widget = QWidget()
        central_widget.setLayout(self._layout)
        self.setCentralWidget(central_widget)

        # Style margins are only resolved once the layout belongs to a widget
        self._default_margins = self._layout.contentsMargins()

        # Fill the combo box and start the first camera
        self._update_cameras()

        # Restore the window position and size if it was previously saved
        geometry = QSettings().value("window/geometry")

        if geometry is not None:
            self.restoreGeometry(geometry)

    def _update_cameras(self):
        """Update the list of available cameras."""
        # Query the currently available cameras
        self._cameras = QMediaDevices.videoInputs()

        # Block signals so repopulating the combo box does not trigger _select_camera
        # repeatedly
        self._camera_combo.blockSignals(True)
        self._camera_combo.clear()
        self._camera_combo.addItems([d.description() for d in self._cameras])
        self._camera_combo.blockSignals(False)

        # The first camera is selected by default
        self._select_camera(0)

    def _select_camera(self, index: int):
        """Select the camera at the given index."""
        self._message_label.hide()

        # Stop and release the previously selected camera
        if self._camera is not None:
            self._camera.stop()
            self._camera = None

        # Create, route to the capture session, and start the camera at the selected
        # index
        if index >= 0 and index < len(self._cameras):
            self._camera = QCamera(self._cameras[index], self)
            self._camera.errorOccurred.connect(self._show_camera_error)
            self._capture_session.setCamera(self._camera)
            self._camera.start()

            # Qt only logs a warning, without emitting an error, when access is denied
            app = QApplication.instance()

            if (
                app and
                app.checkPermission(QCameraPermission()) == Qt.PermissionStatus.Denied
            ):
                self._show_message(CAMERA_ACCESS_DENIED_MESSAGE)

    def _show_camera_error(self, error: QCamera.Error, error_text: str):
        """Show an error message when the camera encounters an error."""
        self._show_message(error_text)

    def _show_message(self, text: str):
        """Show a message in the message label."""
        self._message_label.setText(text)
        self._message_label.show()

    def _enter_presentation_mode(self):
        """Hide the window bar and camera controls, keeping only the video widget."""
        self._presentation_mode = True
        self._controls.hide()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._toggle_bar(False)

    def _exit_presentation_mode(self):
        """Show the window bar and camera controls."""
        self._presentation_mode = False
        self._controls.show()
        self._layout.setContentsMargins(self._default_margins)
        self._toggle_bar(True)

    def _toggle_bar(self, enabled: bool):
        """Toggle the visibility of the window bar."""
        geometry = self.geometry()
        flags = Qt.WindowType.Window

        if not enabled:
            flags |= (
                Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
            )

        # Changing window flags hides the window, so it must be shown again
        self.setWindowFlags(flags)
        self.setGeometry(geometry)
        self.show()

    def mousePressEvent(self, event: QMouseEvent):
        """Start dragging the window in presentation mode."""
        if self._presentation_mode and event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Move the window while the left button is dragged in presentation mode."""
        if self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Stop dragging the window in presentation mode."""
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        """Leave presentation mode when Escape is pressed."""
        if self._presentation_mode and event.key() == Qt.Key.Key_Escape:
            self._exit_presentation_mode()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent):
        """Handle the window close event."""
        # Save the window position and size before closing
        QSettings().setValue("window/geometry", self.saveGeometry())

        # Call the base class implementation to ensure that the window closes properly
        super().closeEvent(event)
