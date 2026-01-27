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
class WorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

class DatabaseWorker(QRunnable):
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
        self.wait(500)
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
        
        # Стиль картки (рамка)
        self.setFixedSize(480, 320)
        self.setStyleSheet("""
            QFrame {
                background-color: #000; 
                border-radius: 12px;
                border: 1px solid #333;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        # Відео лейбл
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("border-radius: 12px; background-color: #050505;")
        self.video_label.setScaledContents(True)
        
        # --- OVERLAY (ШАР ПОВЕРХ ВІДЕО) ---
        overlay_container = QWidget(self.video_label)
        
        # Прозорий фон для контейнера, щоб не було чорної смуги
        overlay_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        overlay_container.setStyleSheet("background: transparent;")
        
        overlay_layout = QHBoxLayout(overlay_container)
        overlay_layout.setContentsMargins(0, 15, 15, 0)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        
        # --- ПЛАШКА З КНОПКАМИ ---
        badges_container = QFrame()
        badges_container.setStyleSheet("background-color: rgba(0, 0, 0, 0.7); border-radius: 4px;")
        
        badges_layout = QHBoxLayout(badges_container)
        badges_layout.setContentsMargins(8, 4, 8, 4)
        badges_layout.setSpacing(12)
        
        # Назва
        name_lbl = QLabel(f"{self.camera.name}")
        name_lbl.setStyleSheet("color: #FFFFFF; font-weight: bold; font-family: Arial; font-size: 13px; background: transparent; border: none;")
        
        # LIVE
        live_lbl = QLabel("● LIVE")
        live_lbl.setStyleSheet("color: #FF5555; font-weight: bold; font-size: 11px; background: transparent; border: none;")
        
        # Розділювач
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setStyleSheet("background-color: rgba(255,255,255,0.3); border: none;")
        line.setFixedWidth(1)
        line.setFixedHeight(12)

        # Кнопка Видалити (ВИПРАВЛЕНО: прибрано transform)
        btn_del = QPushButton("✕")
        btn_del.setFixedSize(20, 20)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton { color: #DDD; border: none; background: transparent; font-weight: bold; font-size: 14px; } 
            QPushButton:hover { color: #FF5555; }
        """)
        btn_del.clicked.connect(self.on_delete_click)

        # Збираємо плашку
        badges_layout.addWidget(name_lbl)
        badges_layout.addWidget(live_lbl)
        badges_layout.addWidget(line)
        badges_layout.addWidget(btn_del)
        
        # Додаємо плашку на прозорий шар
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
        # Оновлюємо геометрію оверлею
        if self.video_label.children():
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
        self.setWindowTitle("PyRTSP Monitor Pro")
        self.resize(1280, 800)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #121215; }
            
            QFrame#sidebar { 
                background-color: #1E1E24; 
                border-right: 1px solid #2A2A35; 
                min-width: 220px; 
                max-width: 220px; 
            }
            
            QPushButton.menuBtn { 
                text-align: left; 
                padding: 14px 24px; 
                color: #A0A0B0; 
                border: none; 
                border-radius: 8px; 
                margin: 6px 12px; 
                font-size: 14px; 
                font-family: Arial;
                font-weight: 500;
            }
            QPushButton.menuBtn:hover { background-color: #2A2A35; color: white; }
            QPushButton.menuBtn[active="true"] { background-color: #6C5CE7; color: white; font-weight: bold; }
            
            QFrame#contentPanel { background-color: transparent; border: none; }
            QLabel#sectionHeader { color: #FFFFFF; font-size: 22px; font-weight: 600; font-family: Arial; }
            
            QScrollBar:vertical {
                border: none; background: #121215; width: 8px; margin: 0px;
            }
            QScrollBar::handle:vertical { background: #333; min-height: 20px; border-radius: 4px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
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
        sb_layout.setContentsMargins(0, 30, 0, 30)
        
        lbl_logo = QLabel("PyRTSP\nMonitor")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_logo.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        sb_layout.addWidget(lbl_logo)
        
        btn_cams = QPushButton("Камери")
        btn_cams.setProperty("class", "menuBtn")
        btn_cams.setProperty("active", True)
        sb_layout.addWidget(btn_cams)
        
        sb_layout.addStretch()
        
        user_lbl = QLabel(f"👤 {self.username}")
        user_lbl.setStyleSheet("color: #666; font-size: 12px; margin-left: 24px; margin-bottom: 5px;")
        sb_layout.addWidget(user_lbl)

        btn_exit = QPushButton("Вихід")
        btn_exit.setProperty("class", "menuBtn")
        btn_exit.clicked.connect(self.close)
        sb_layout.addWidget(btn_exit)
        
        main_layout.addWidget(sidebar)

        # Content
        content_frame = QFrame()
        content_frame.setObjectName("contentPanel")
        cf_layout = QVBoxLayout(content_frame)
        cf_layout.setContentsMargins(40, 40, 40, 0)
        
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Активні Трансляції", objectName="sectionHeader"))
        top_row.addStretch()
        
        btn_add = QPushButton("+ Додати камеру")
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #2D2D3A; color: white; font-size: 14px; 
                padding: 10px 20px; border-radius: 8px; border: 1px solid #3D3D4A; font-weight: 600;
            }
            QPushButton:hover { background-color: #3D3D4A; border-color: #555; }
        """)
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self.open_add_dialog)
        top_row.addWidget(btn_add)
        
        cf_layout.addLayout(top_row)
        cf_layout.addSpacing(20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        
        self.video_grid = QGridLayout(self.grid_widget)
        self.video_grid.setSpacing(24)
        self.video_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        scroll.setWidget(self.grid_widget)
        cf_layout.addWidget(scroll)

        main_layout.addWidget(content_frame, 1)

    def load_cameras(self):
        QTimer.singleShot(10, self._load_cameras_impl)

    def _load_cameras_impl(self):
        db_cameras = self.repo.get_all()
        existing_ids = {str(w.camera.id) for w in self.widgets}
        
        for cam in db_cameras:
            if str(cam.id) not in existing_ids:
                wid = VideoFeedWidget(cam)
                wid.delete_requested.connect(self.handle_delete_camera)
                wid.start()
                self.widgets.append(wid)
        
        self._reflow_grid()

    def _reflow_grid(self):
        max_cols = 2
        for index, widget in enumerate(self.widgets):
            row = index // max_cols
            col = index % max_cols
            self.video_grid.addWidget(widget, row, col)

    def handle_delete_camera(self, camera):
        reply = QMessageBox.question(
            self, "Підтвердження", f"Ви впевнені, що хочете видалити камеру\n'{camera.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            widget_to_remove = next((w for w in self.widgets if w.camera.id == camera.id), None)
            
            if widget_to_remove:
                widget_to_remove.stop()
                self.video_grid.removeWidget(widget_to_remove)
                widget_to_remove.setParent(None)
                widget_to_remove.deleteLater()
                self.widgets.remove(widget_to_remove)
                self._reflow_grid()
            
            worker = DatabaseWorker(self.repo.delete, camera.id)
            QThreadPool.globalInstance().start(worker)

    def open_add_dialog(self):
        d = AddCameraDialog(self)
        if d.exec():
            self.load_cameras()

    def closeEvent(self, e):
        for w in self.widgets: w.stop()
        e.accept()