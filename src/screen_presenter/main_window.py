from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QMainWindow


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(QApplication.applicationDisplayName())
        self.setMinimumSize(100, 100)
        self.resize(400, 300)

        # Restore the window position and size if it was previously saved
        geometry = QSettings().value("window/geometry")

        if geometry is not None:
            self.restoreGeometry(geometry)

    def closeEvent(self, event):
        # Save the window position and size before closing
        QSettings().setValue("window/geometry", self.saveGeometry())

        # Call the base class implementation to ensure that the window closes properly
        super().closeEvent(event)
