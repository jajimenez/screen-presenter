import sys

from PySide6.QtWidgets import QApplication

from screen_presenter.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Start the application's event loop
    sys.exit(app.exec())
