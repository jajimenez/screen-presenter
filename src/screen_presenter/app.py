import ctypes
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from screen_presenter.main_window import MainWindow

# In MacOS, icons usually have transparent padding
LOGO_NAME = "logo-macos.svg" if sys.platform == "darwin" else "logo.svg"
LOGO_PATH = Path(__file__).parent / "resources" / LOGO_NAME
APP_ID = "screen-presenter"


def main():
    # Windows groups the taskbar button under python.exe (with its icon) unless the
    # process declares its own ID; this must happen before any window is created.
    # ctypes.windll only exists on Windows, so this must be guarded by a platform check.
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)

    # Set up the application
    app = QApplication(sys.argv)
    app.setOrganizationName("screen-presenter")
    app.setApplicationName("screen-presenter")
    app.setApplicationDisplayName("Screen Presenter")
    app.setDesktopFileName(APP_ID)  # Linux/Wayland app ID, matched to a .desktop file
    app.setWindowIcon(QIcon(str(LOGO_PATH)))

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Start the application's event loop
    sys.exit(app.exec())
