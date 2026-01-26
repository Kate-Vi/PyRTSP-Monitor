import sys
import gi
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QPushButton, QFrame, QScrollArea, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QRunnable, QThreadPool, QObject
from PyQt6.QtGui import QImage, QPixmap

# --- GStreamer Check ---
try:
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst, GLib
    Gst.init(None)
except Exception:
    pass

from dal.repository import CameraRepository
from bll.pipeline_builder import PipelineBuilder
from ui.add_camera_dialog import AddCameraDialog

# ==========================================
# 1. DATABASE WORKER
# ==========================================

#NEW

class WorkerSignals(QObject):
    """Окремий клас для сигналів, бо QRunnable не вміє їх емітувати"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

class DatabaseWorker(QRunnable):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals() # Ініціалізуємо сигнали
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))

# ==========================================
# 2. ВІДЕО ПОТІК
# ==========================================
class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self, camera_model):
        super().__init__()
        self.camera = camera_model
        self.pipeline = None
        self.is_running = True

    def run(self):
        try:
            pipeline_str = PipelineBuilder.build(self.camera)
            self.pipeline = Gst.parse_launch(pipeline_str)
            appsink = self.pipeline.get_by_name("sink")
            appsink.set_property("emit-signals", True)
            appsink.connect("new-sample", self.on_new_sample)
            self.pipeline.set_state(Gst.State.PLAYING)
            
            bus = self.pipeline.get_bus()
            while self.is_running:
                # Читаємо повідомлення з таймаутом, щоб не зависати
                msg = bus.timed_pop(100 * Gst.MSECOND)
                if msg:
                    if msg.type == Gst.MessageType.ERROR or msg.type == Gst.MessageType.EOS:
                        break
        except Exception as e:
            print(f"Video Error: {e}")
        finally:
            if self.pipeline:
                self.pipeline.set_state(Gst.State.NULL)

    def on_new_sample(self, sink):
        sample = sink.emit("pull-sample")
        if not sample: return Gst.FlowReturn.ERROR
        
        buf = sample.get_buffer()
        caps = sample.get_caps()
        h = caps.get_structure(0).get_value("height")
        w = caps.get_structure(0).get_value("width")
        buffer = buf.extract_dup(0, buf.get_size())
        q_image = QImage(buffer, w, h, QImage.Format.Format_BGR888)
        self.change_pixmap_signal.emit(q_image)
        return Gst.FlowReturn.OK

    def stop(self):
        self.is_running = False
        self.wait(500) # Чекаємо максимум 0.5с
        if self.isRunning():
            self.terminate()

# ==========================================
# 3. ВІДЖЕТ КАМЕРИ
# ==========================================
class VideoFeedWidget(QFrame):
    delete_requested = pyqtSignal(object)

    def __init__(self, camera, parent=None):
        super().__init__(parent)
        self.camera = camera
        self.thread = None
        self.setProperty("class", "videoCard")
        
        # 👇 ФІКС РОЗМІРУ: Фіксуємо розмір картки, щоб вона не розтягувалась
        self.setFixedSize(480, 320)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("border-radius: 4px; background-color: #050505;")
        self.video_label.setScaledContents(True)
        
        # Overlay
        overlay_container = QWidget(self.video_label)
        overlay_layout = QHBoxLayout(overlay_container)
        overlay_layout.setContentsMargins(0, 10, 10, 0)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        
        # Бейджі
        badges_container = QFrame()
        badges_container.setStyleSheet("background-color: rgba(0, 0, 0, 0.7); border-radius: 4px;")
        badges_layout = QHBoxLayout(badges_container)
        badges_layout.setContentsMargins(5, 5, 5, 5)
        badges_layout.setSpacing(10)
        
        name_lbl = QLabel(f"{self.camera.name}")
        name_lbl.setStyleSheet("color: white; font-weight: bold; font-family: Arial; border: none; background: transparent;")
        
        self.live_lbl = QLabel("LIVE")
        self.live_lbl.setStyleSheet("color: white; background-color: #DA3633; font-weight: bold; font-size: 11px; padding: 2px 6px; border-radius: 2px;")
        
        btn_del = QPushButton("X")
        btn_del.setFixedSize(20, 20)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet("QPushButton { color: #8B949E; border: none; background: transparent; font-weight: bold; } QPushButton:hover { color: #F85149; }")
        btn_del.clicked.connect(self.on_delete_click)

        badges_layout.addWidget(name_lbl)
        badges_layout.addWidget(self.live_lbl)
        badges_layout.addWidget(btn_del)
        
        overlay_layout.addWidget(badges_container)
        layout.addWidget(self.video_label)

    def on_delete_click(self):
        self.delete_requested.emit(self.camera)

    def start(self):
        if not self.thread:
            self.thread = VideoThread(self.camera)
            self.thread.change_pixmap_signal.connect(self.update_img)
            self.thread.start()

    def update_img(self, img):
        self.video_label.setPixmap(QPixmap.fromImage(img))
        if self.video_label.children():
            # Оновлюємо ширину оверлею під ширину віджета
            self.video_label.children()[0].setGeometry(0, 0, self.width(), 60)

    def stop(self):
        if self.thread:
            self.thread.stop()
            self.thread = None

# ==========================================
# 4. ГОЛОВНЕ ВІКНО
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self.repo = CameraRepository()
        self.widgets = []
        self.init_ui()
        self.load_cameras()

    def init_ui(self):
        self.setWindowTitle("PyRTSP Monitor")
        self.resize(1200, 750)
        self.setStyleSheet("""
            QMainWindow { background-color: #0F1115; }
            QFrame#sidebar { background-color: #161B22; border-right: 1px solid #21262D; min-width: 200px; max-width: 200px; }
            QPushButton.menuBtn { text-align: left; padding: 12px 20px; color: #8B949E; border: none; border-radius: 6px; margin: 4px 10px; font-size: 14px; font-family: Arial; }
            QPushButton.menuBtn:hover { color: white; background-color: #21262D; }
            QPushButton.menuBtn[active="true"] { background-color: #238636; color: white; font-weight: bold; }
            QFrame#contentPanel { background-color: #0D1117; border-top: none; }
            QLabel#sectionHeader { color: white; font-size: 18px; font-weight: bold; }
            QFrame.videoCard { background-color: #000; border-radius: 4px; border: 1px solid #30363D; }
        """)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(10, 20, 10, 20)
        
        btn_cams = QPushButton("Камери")
        btn_cams.setProperty("class", "menuBtn")
        btn_cams.setProperty("active", True)
        sb_layout.addWidget(btn_cams)
        sb_layout.addStretch()
        btn_exit = QPushButton("Вихід")
        btn_exit.setProperty("class", "menuBtn")
        btn_exit.clicked.connect(self.close)
        sb_layout.addWidget(btn_exit)
        main_layout.addWidget(sidebar)

        # Content
        content_frame = QFrame()
        content_frame.setObjectName("contentPanel")
        cf_layout = QVBoxLayout(content_frame)
        cf_layout.setContentsMargins(30, 30, 30, 30)
        
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Камери", objectName="sectionHeader"))
        top_row.addStretch()
        btn_add = QPushButton("+")
        btn_add.setStyleSheet("background: transparent; color: #C9D1D9; font-size: 28px; border: none; font-weight: light;")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self.open_add_dialog)
        top_row.addWidget(btn_add)
        cf_layout.addLayout(top_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        
        # 👇 ГОЛОВНА ЗМІНА ДЛЯ ДИЗАЙНУ:
        self.video_grid = QGridLayout(self.grid_widget)
        self.video_grid.setSpacing(20)
        # Притискаємо елементи ВЛІВО і ВГОРУ (щоб не розповзалися)
        self.video_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        scroll.setWidget(self.grid_widget)
        cf_layout.addWidget(scroll)
        main_layout.addWidget(content_frame, 1)

    def load_cameras(self):
        # Асинхронне завантаження, щоб не блокувати UI
        QTimer.singleShot(10, self._load_cameras_impl)

    def _load_cameras_impl(self):
        # 1. Отримуємо свіжий список з БД
        db_cameras = self.repo.get_all()
        
        # 2. Складаємо список ID камер, які вже є на екрані
        existing_ids = set()
        for w in self.widgets:
            existing_ids.add(str(w.camera.id))
        
        # 3. Знаходимо та створюємо ТІЛЬКИ нові віджети
        new_widgets_count = 0
        for cam in db_cameras:
            if str(cam.id) not in existing_ids:
                # Створюємо віджет
                wid = VideoFeedWidget(cam)
                wid.delete_requested.connect(self.handle_delete_camera)
                wid.start() # Запускаємо потік
                
                # Додаємо у внутрішній список пам'яті
                self.widgets.append(wid)
                new_widgets_count += 1
        
        if new_widgets_count == 0 and len(db_cameras) == len(self.widgets):
            # Якщо нічого не змінилося - виходимо, щоб не смикати сітку
            return

        # 4. ПЕРЕРАХУНОК ПОЗИЦІЙ (Re-Layout)
        # Ми беремо ВСІ віджети і заново кажемо сітці, де вони мають стояти.
        # Qt досить розумний: якщо віджет вже там, він не буде мигати.
        
        max_cols = 2  # <--- 2 камери в ряд
        
        for index, wid in enumerate(self.widgets):
            row = index // max_cols
            col = index % max_cols
            
            # Ця команда перемістить віджет, якщо він був не на своєму місці,
            # або залишить як є, якщо місце правильне.
            self.video_grid.addWidget(wid, row, col)
            
        print(f"Оновлено сітку: {len(self.widgets)} камер. Додано нових: {new_widgets_count}")

    def _reflow_grid(self):
        """Перераховує позиції всіх камер у сітці, щоб прибрати дирки."""
        max_cols = 2
        
        # Ми просто проходимось по списку, який у нас залишився
        for index, widget in enumerate(self.widgets):
            row = index // max_cols
            col = index % max_cols
            
            # Ця магія Qt: якщо віджет вже є в лейауті, 
            # addWidget автоматично перемістить його в нову клітинку.
            self.video_grid.addWidget(widget, row, col)

    def handle_delete_camera(self, camera):
        reply = QMessageBox.question(
            self, "Видалення", f"Видалити камеру '{camera.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 1. Знаходимо віджет у списку
            widget_to_remove = None
            for w in self.widgets:
                if w.camera.id == camera.id:
                    widget_to_remove = w
                    break
            
            if widget_to_remove:
                # 2. Зупиняємо і прибираємо з UI
                widget_to_remove.stop()
                self.video_grid.removeWidget(widget_to_remove)
                widget_to_remove.setParent(None)
                widget_to_remove.deleteLater() # Плануємо знищення об'єкта
                
                # 3. Видаляємо зі списку пам'яті
                self.widgets.remove(widget_to_remove)
                
                # 4. ДЕФРАГМЕНТАЦІЯ (Зсуваємо решту камер)
                self._reflow_grid()
            
            # 5. Видаляємо з БД (асинхронно)
            worker = DatabaseWorker(self.repo.delete, camera.id)
            worker.signals.error.connect(lambda e: print(f"Delete Error: {e}"))
            QThreadPool.globalInstance().start(worker)

    def open_add_dialog(self):
        d = AddCameraDialog(self)
        if d.exec():
            self.load_cameras()

    def closeEvent(self, e):
        for w in self.widgets: w.stop()
        e.accept()