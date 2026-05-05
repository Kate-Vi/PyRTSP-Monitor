from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from dal.models import Camera

class AddCameraDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Додати нову камеру")
        self.setFixedSize(400, 350)
        self.init_ui()

    def init_ui(self):
        # Стилізація під темну тему вашого MacBook Air
        self.setStyleSheet("""
            QDialog {
                background-color: #121215;
            }
            QLabel {
                color: #A0A0B0;
                font-size: 14px;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #1E1E24;
                color: white;
                border: 1px solid #333;
                padding: 12px;
                border-radius: 8px;
            }
            QLineEdit:focus {
                border: 1px solid #6C5CE7;
            }
            QPushButton#btnSave {
                background-color: #6C5CE7;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton#btnCancel {
                background-color: transparent;
                color: #888;
                border: 1px solid #444;
                padding: 12px;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Нова камера")
        title.setStyleSheet("color: white; font-size: 20px; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Поле для назви
        layout.addWidget(QLabel("Назва камери"))
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Наприклад: телефон")
        layout.addWidget(self.inp_name)

        # Поле для посилання
        layout.addWidget(QLabel("RTSP URL або назва пристрою"))
        self.inp_url = QLineEdit()
        self.inp_url.setPlaceholderText("rtsp://...")
        layout.addWidget(self.inp_url)

        layout.addStretch()

        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.btn_cancel = QPushButton("Скасувати")
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("Зберегти")
        self.btn_save.setObjectName("btnSave")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self.handle_accept)
        
        buttons_layout.addWidget(self.btn_cancel)
        buttons_layout.addWidget(self.btn_save)
        layout.addLayout(buttons_layout)

    def handle_accept(self):
        """Валідація та збереження камери з урахуванням поля rtsp_url."""
        name = self.inp_name.text().strip()
        url = self.inp_url.text().strip()

        if not name or not url:
            QMessageBox.warning(self, "Помилка", "Будь ласка, заповніть усі поля")
            return

        try:
            # Перевірка унікальності в репозиторії
            existing_cameras = self.parent().repo.get_all()
            for cam in existing_cameras:
                if cam.name.lower() == name.lower():
                    QMessageBox.warning(self, "Помилка", f"Назва '{name}' вже існує")
                    return
                if cam.rtsp_url == url:
                    QMessageBox.warning(self, "Помилка", "Це посилання вже використовується")
                    return
            
            # Створення об'єкта (ВАЖЛИВО: rtsp_url має відповідати вашій моделі)
            new_camera = Camera(
                name=name, 
                rtsp_url=url, 
                protocol="tcp"
            )
            
            # Додавання в базу даних
            self.parent().repo.add(new_camera)
            
            print(f"✅ Камеру '{name}' додано успішно!")
            self.accept() 
            
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося зберегти: {e}")