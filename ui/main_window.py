import sys
import gi
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QPushButton, QFrame, QScrollArea, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QImage, QPixmap

# --- GStreamer Ініціалізація ---
try:
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
    Gst.init(None)
except Exception as e:
    print(f"GStreamer init error: {e}")

from dal.repository import CameraRepository
from bll.pipeline_builder import PipelineBuilder
from ui.add_camera_dialog import AddCameraDialog
from ui.add_camera_dialog import AddCameraDialog

# ==========================================
# 1. ВІДЕО ПОТІК (GStreamer -> PyQt6)
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
            if not appsink:
                return

            appsink.set_property("emit-signals", True)
            appsink.connect("new-sample", self.on_new_sample)
            
            self.pipeline.set_state(Gst.State.PLAYING)
            
            bus = self.pipeline.get_bus()
            while self.is_running:
                msg = bus.timed_pop(100 * Gst.MSECOND)
                if msg and (msg.type == Gst.MessageType.ERROR or msg.type == Gst.MessageType.EOS):
                    break
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
        
        success, map_info = buf.map(Gst.MapFlags.READ)
        if success:
            q_image = QImage(map_info.data, w, h, QImage.Format.Format_BGR888).copy()
            self.change_pixmap_signal.emit(q_image)
            buf.unmap(map_info)
        return Gst.FlowReturn.OK

    def stop(self):
        self.is_running = False
        self.wait(500)

# ==========================================
# 2. ВІДЖЕТ КАМЕРИ (З виправленим розширенням)
# ==========================================
class VideoFeedWidget(QFrame):
    delete_requested = pyqtSignal(object)

    def __init__(self, camera, parent=None):
        super().__init__(parent)
        self.camera = camera
        self.thread = None
        
        self.setFixedSize(480, 320)
        self.setStyleSheet("QFrame { background-color: #000; border-radius: 12px; border: 1px solid #333; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        # Місце для відео
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setScaledContents(False) # ВИМКНЕНО автоматичне розтягування
        self.video_label.setStyleSheet("background-color: #050505; border-radius: 12px;")
        
        # Оверлей (Назва та кнопка видалення)
        self.overlay = QFrame(self.video_label)
        self.overlay.setGeometry(0, 0, 480, 50)
        self.overlay.setStyleSheet("background: transparent; border: none;")
        
        overlay_layout = QHBoxLayout(self.overlay)
        name_lbl = QLabel(f" {self.camera.name} ")
        name_lbl.setStyleSheet("color: white; font-weight: bold; background: rgba(0,0,0,0.6); border-radius: 4px;")
        
        btn_del = QPushButton("✕")
        btn_del.setFixedSize(26, 26)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet("color: white; background: rgba(220,50,50,0.8); border-radius: 13px; border: none;")
        btn_del.clicked.connect(self.on_delete_click)
        
        overlay_layout.addWidget(name_lbl)
        overlay_layout.addStretch()
        overlay_layout.addWidget(btn_del)
        
        layout.addWidget(self.video_label)

    def update_img(self, img):
        """Розумне масштабування із збереженням пропорцій."""
        if img.isNull(): return
        
        # Масштабуємо картинку під розмір лейбла, зберігаючи Aspect Ratio
        pixmap = QPixmap.fromImage(img)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation # Для чіткості картинки
        )
        self.video_label.setPixmap(scaled_pixmap)

    def on_delete_click(self):
        self.delete_requested.emit(self.camera)

    def start(self):
        if not self.thread:
            self.thread = VideoThread(self.camera)
            self.thread.change_pixmap_signal.connect(self.update_img)
            self.thread.start()

    def stop(self):
        if self.thread:
            self.thread.stop()
            self.thread = None

# ==========================================
# 3. ГОЛОВНЕ ВІКНО
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
        self.resize(1200, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0,0,0,0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("background-color: #1E1E24;")
        side_layout = QVBoxLayout(sidebar)
        
        logo = QLabel("PyRTSP\nMonitor")
        logo.setStyleSheet("color: white; font-weight: bold; font-size: 18px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(logo)

        btn_add = QPushButton("+ Додати камеру")
        btn_add.setStyleSheet("background: #6C5CE7; color: white; padding: 10px; border-radius: 5px;")
        btn_add.clicked.connect(self.open_add_dialog)
        side_layout.addWidget(btn_add)
        side_layout.addStretch()
        layout.addWidget(sidebar)

        # Content Area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        title = QLabel("Активні Трансляції")
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        content_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.video_grid = QGridLayout(self.grid_container)
        self.video_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self.grid_container)
        content_layout.addWidget(scroll)
        
        layout.addWidget(content)

    def load_cameras(self):
        for cam in self.repo.get_all():
            wid = VideoFeedWidget(cam)
            wid.delete_requested.connect(self.handle_delete_camera)
            wid.start()
            self.widgets.append(wid)
        self._reflow_grid()

    def _reflow_grid(self):
        for i in reversed(range(self.video_grid.count())):
            self.video_grid.itemAt(i).widget().setParent(None)
        for idx, w in enumerate(self.widgets):
            self.video_grid.addWidget(w, idx // 2, idx % 2)

    def handle_delete_camera(self, camera):
        res = QMessageBox.question(self, "Видалення", f"Видалити {camera.name}?")
        if res == QMessageBox.StandardButton.Yes:
            w = next(x for x in self.widgets if x.camera.id == camera.id)
            w.stop()
            self.widgets.remove(w)
            w.deleteLater()
            self.repo.delete(camera.id)
            self._reflow_grid()

    def open_add_dialog(self):
        if AddCameraDialog(self).exec():
            # Очищаємо старі і завантажуємо наново для простоти
            for w in self.widgets: w.stop(); w.deleteLater()
            self.widgets.clear()
            self.load_cameras()

    def closeEvent(self, e):
        for w in self.widgets: w.stop()
        e.accept()