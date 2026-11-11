from PySide6.QtCore import QPoint, QSettings, Qt
from PySide6.QtGui import QCloseEvent, QKeyEvent, QMouseEvent
from PySide6.QtMultimedia import QMediaCaptureSession
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

from screen_presenter.camera_controller import CameraController

GEOMETRY_SETTING = "window/geometry"


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the main window."""
        # Set before the base initializer so Qt events can never see them missing
        self._presentation_mode = False
        self._drag_offset: QPoint | None = None

        super().__init__(parent)

        self.setWindowTitle(QApplication.applicationDisplayName())
        self.setMinimumSize(150, 150)
        self.resize(400, 300)

        self._build_ui()

        self._camera_controller = CameraController(self._capture_session, self)
        self._camera_controller.cameras_changed.connect(self._show_cameras)
        self._camera_controller.error_changed.connect(self._show_message)
        self._camera_controller.selected_camera_available_changed.connect(
            self._present_button.setEnabled
        )
        # The system prompt returns focus to the terminal, hiding the window behind it
        self._camera_controller.permission_answered.connect(self._bring_to_front)
        self._camera_combo.currentIndexChanged.connect(self._camera_controller.select)

        # Fill the combo box and start the first camera
        self._camera_controller.update()

        self._restore_settings()

    def _build_ui(self) -> None:
        """Create the widgets and layouts."""
        # Camera selection combo box
        self._camera_combo = QComboBox()

        # Button to enter presentation mode
        self._present_button = QPushButton("Present")
        # Enabled once the selected camera is running
        self._present_button.setEnabled(False)
        self._present_button.clicked.connect(self._enter_presentation_mode)

        # Layout for the controls (camera combo box and present button)
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.addWidget(self._camera_combo, 1)
        controls_layout.addWidget(self._present_button)

        self._controls = QWidget()
        self._controls.setLayout(controls_layout)

        # Video display widget
        self._video_widget = QVideoWidget()
        self._video_widget.setAspectRatioMode(
            Qt.AspectRatioMode.KeepAspectRatioByExpanding
        )

        # Message shown when the camera cannot be used, such as when access is denied
        self._message_label = QLabel()
        self._message_label.setWordWrap(True)
        self._message_label.hide()

        # Capture pipeline: camera -> capture session -> video widget
        self._capture_session = QMediaCaptureSession(self)
        self._capture_session.setVideoOutput(self._video_widget)

        # Stack the selector above the video preview
        self._layout = QVBoxLayout()
        self._layout.addWidget(self._controls)
        self._layout.addWidget(self._message_label)
        self._layout.addWidget(self._video_widget, 1)

        central_widget = QWidget()
        central_widget.setLayout(self._layout)
        self.setCentralWidget(central_widget)

        # Style margins are only resolved once the layout belongs to a widget
        self._default_margins = self._layout.contentsMargins()

    def _restore_settings(self) -> None:
        """Restore the window position and size if they were previously saved."""
        geometry = QSettings().value(GEOMETRY_SETTING)

        if geometry is not None:
            self.restoreGeometry(geometry)

    def _show_cameras(self, names: list[str], selected_index: int) -> None:
        """Show the camera names in the combo box with the given one selected.

        Args:
            names: List of camera names to display.
            selected_index: Index of the currently selected camera.
        """
        # Block signals so repopulating does not select a camera again
        self._camera_combo.blockSignals(True)
        self._camera_combo.clear()
        self._camera_combo.addItems(names)
        self._camera_combo.setCurrentIndex(selected_index)
        self._camera_combo.blockSignals(False)

    def _bring_to_front(self) -> None:
        self.raise_()
        self.activateWindow()

    def _show_message(self, text: str) -> None:
        """Show a message in the message label, or hide it if the text is empty."""
        self._message_label.setText(text)
        self._message_label.setVisible(bool(text))

    def _enter_presentation_mode(self) -> None:
        """Hide the window bar and camera controls, keeping only the video widget."""
        self._presentation_mode = True
        self._controls.hide()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._toggle_bar(False)

    def _exit_presentation_mode(self) -> None:
        """Show the window bar and camera controls."""
        self._presentation_mode = False
        self._controls.show()
        self._layout.setContentsMargins(self._default_margins)
        self._toggle_bar(True)

    def _toggle_bar(self, enabled: bool) -> None:
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

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start dragging the window in presentation mode."""
        if self._presentation_mode and event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Move the window while the left button is dragged in presentation mode."""
        if self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Stop dragging the window in presentation mode."""
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Leave presentation mode when Escape is pressed."""
        if self._presentation_mode and event.key() == Qt.Key.Key_Escape:
            self._exit_presentation_mode()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Save the window position and size before closing."""
        QSettings().setValue(GEOMETRY_SETTING, self.saveGeometry())
        super().closeEvent(event)
