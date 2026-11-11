import sys

from PySide6.QtCore import QLoggingCategory
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from screen_presenter.main_window import MainWindow
from screen_presenter.platform_support import get_logo_path, set_up_platform

APP_ID = "screen-presenter"


def main():
    # Must happen before creating the QApplication instance
    set_up_platform(APP_ID)

    # Hide the FFmpeg backend's startup info line; warnings and errors still show
    QLoggingCategory.setFilterRules("qt.multimedia.ffmpeg.info=false")

    # Set up the application
    app = QApplication(sys.argv)
    app.setOrganizationName("screen-presenter")
    app.setApplicationName("screen-presenter")
    app.setApplicationDisplayName("Screen Presenter")
    # Only used on Linux with Wayland, to match the app ID to a .desktop file; ignored
    # elsewhere
    app.setDesktopFileName(APP_ID)
    app.setWindowIcon(QIcon(str(get_logo_path())))

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Bring the window to the front in case it was hidden by the system permission prompt
    window.raise_()
    window.activateWindow()

    # Start the application's event loop
    sys.exit(app.exec())
