from PyQt5.QtWidgets import (
    QLabel, QDialog, QVBoxLayout, QProgressBar, QApplication
)
from PyQt5.QtCore import Qt


class LoadingSpinner(QDialog):
    def __init__(self, message="⏳ Suche läuft..."):
        super().__init__()
        self.setWindowTitle("Bitte warten")
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        self.setModal(True)

        self.layout = QVBoxLayout()
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignCenter)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # infinite spinner

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.progress)
        self.setLayout(self.layout)
        self.resize(300, 100)
        self.center()

    def center(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2
        )
