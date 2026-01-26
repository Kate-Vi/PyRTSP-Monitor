from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QRunnable, QThreadPool, QObject, pyqtSignal
from dal.repository import CameraRepository
from dal.models import Camera


class WorkerSignals(QObject):
    """
    QRunnable не може мати сигналів, тому ми створюємо для них окремий клас-обгортку.
    """
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

class DatabaseWorker(QRunnable):
    """Асинхронний робітник для операцій з БД"""
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
    
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))
class AddCameraDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.repo = CameraRepository()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Додати камеру")
        self.setFixedSize(400, 250)
        
        self.setStyleSheet("""
            QDialog { background-color: #161B22; color: white; }
            QLabel { font-size: 14px; color: #C9D1D9; font-weight: bold; }
            QLineEdit { 
                padding: 8px; background-color: #0D1117; 
                border: 1px solid #30363D; border-radius: 6px; color: white;
            }
            QPushButton {
                padding: 10px; border-radius: 6px; font-weight: bold;
            }
            QPushButton#btnSave { background-color: #238636; color: white; border: none; }
            QPushButton#btnSave:hover { background-color: #2ea043; }
            QPushButton#btnCancel { background-color: #21262D; color: #C9D1D9; border: 1px solid #30363D; }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        layout.addWidget(QLabel("Назва камери:"))
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Наприклад: Головний вхід")
        layout.addWidget(self.inp_name)

        layout.addWidget(QLabel("RTSP посилання:"))
        self.inp_rtsp = QLineEdit()
        self.inp_rtsp.setPlaceholderText("rtsp://admin:12345@192.168.1.10...")
        layout.addWidget(self.inp_rtsp)

        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Скасувати")
        btn_cancel.setObjectName("btnCancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("Зберегти")
        btn_save.setObjectName("btnSave")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self.save_camera)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def save_camera(self):
        name = self.inp_name.text().strip()
        rtsp = self.inp_rtsp.text().strip()

        if not name or not rtsp:
            QMessageBox.warning(self, "Помилка", "Будь ласка, заповніть всі поля!")
            return

        self.setEnabled(False)
        
        try:
            new_cam = Camera(name=name, rtsp_url=rtsp)
        except Exception as e:
            QMessageBox.critical(self, "Валідація", str(e))
            self.setEnabled(True)
            return
        self._start_worker(new_cam)
        

    def _start_worker(self, new_cam):
            # 1. Створюємо воркера.
            # УВАГА: new_cam передається просто як другий аргумент. 
            # Він потрапить у *args воркера. Ніяких args=(...)
            worker = DatabaseWorker(self.repo.add, new_cam)
            
            # 2. Підключаємо слоти (вони виконаються в Main Thread)
            worker.signals.finished.connect(self._on_camera_added)
            worker.signals.error.connect(self._on_camera_add_error)
            
            # 3. Стартуємо
            QThreadPool.globalInstance().start(worker)


    def _on_camera_added(self, result):
        """Успішне додавання камери"""
        print(f"✅ Камеру успішно додано в БД!")
        self.accept()

    def _on_camera_add_error(self, error):
        """Помилка при додаванні камери"""
        print(f"❌ Помилка збереження: {error}")
        QMessageBox.critical(self, "Помилка бази даних", f"Не вдалося зберегти камеру:\n{error}")
        self.setEnabled(True)