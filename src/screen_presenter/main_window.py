from PySide6.QtWidgets import QMainWindow


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Screen Presenter")
        self.setMinimumSize(100, 100)
        self.resize(400, 300)
