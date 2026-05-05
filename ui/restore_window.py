from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal

class RestoreWindow(QWidget):
    # Сигнал для повернення
    on_back_click = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        # ... (ваш інтерфейс відновлення)

        btn_back = QPushButton("Повернутися до входу")
        btn_back.clicked.connect(self.on_back_click.emit)
        layout.addWidget(btn_back)