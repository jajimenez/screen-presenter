from PySide6.QtCore import Qt
from PySide6.QtGui import QBitmap, QPixmap, QRegion
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from screen_presenter._version import version
from screen_presenter.platform_support import get_logo_path

INFO_TEXT = (
    "<h3>{}</h3>"
    "<p>Version {}</p>"
    "<p>Shows your camera as a presenter overlay while you record your screen.</p>"
    "<p>Copyright © 2026 Jose A. Jimenez</p>"
    "<p>Licensed under the MIT License.</p>"
)

class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the about dialog."""
        super().__init__(parent)

        self.setWindowTitle(f"About {QApplication.applicationDisplayName()}")
        self.setModal(True)

        self._build_ui()

    def _build_ui(self) -> None:
        """Create the widgets and layouts."""
        # Application logo, cropped to its visible pixels to drop the SVG padding
        logo_image = QPixmap(str(get_logo_path())).toImage()
        visible_area = QRegion(QBitmap.fromImage(logo_image.createAlphaMask()))

        logo = QPixmap.fromImage(logo_image.copy(visible_area.boundingRect()))
        logo_label = QLabel()
        logo_label.setPixmap(
            logo.scaledToWidth(96, Qt.TransformationMode.SmoothTransformation)
        )

        # Application information
        info_label = QLabel(
            INFO_TEXT.format(QApplication.applicationDisplayName(), version)
        )
        info_label.setWordWrap(True)
        info_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        info_label.setOpenExternalLinks(True)

        # Layout for the content (logo and information)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        content_layout.addWidget(logo_label, 0, Qt.AlignmentFlag.AlignTop)
        content_layout.addWidget(info_label, 1)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)

        # Main layout for the dialog
        layout = QVBoxLayout(self)
        layout.addLayout(content_layout)
        layout.addWidget(buttons)
