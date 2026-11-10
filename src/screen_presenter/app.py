import sys

from PySide6.QtWidgets import QApplication

from screen_presenter.main_window import MainWindow


def main():
    # Set up the application
    app = QApplication(sys.argv)
    app.setOrganizationName("screen-presenter")
    app.setApplicationName("screen-presenter")
    app.setApplicationDisplayName("Screen Presenter")

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Start the application's event loop
    sys.exit(app.exec())
