import sys
import gi

try:
    gi.require_version('Gst', '1.0')
    gi.require_version('GstRtspServer', '1.0')
    from gi.repository import Gst, GstRtspServer
    Gst.init(None)
except Exception as e:
    print(f"Помилка ініціалізації GStreamer: {e}")

from PyQt6.QtWidgets import QApplication, QStackedWidget
from PyQt6.QtCore import Qt, QTimer
import config
from bll.pipeline_builder import USBRTSPFactory
from ui.login_window import LoginWindow
from ui.register_window import RegisterWindow
from ui.restore_window import RestoreWindow
from ui.main_window import MainWindow

class PyRTSPController(QStackedWidget):
    """
    Головний контролер екранів (Single Window Architecture).
    Керує перемиканням між авторизацією та моніторингом в одному вікні.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyRTSP Monitor Pro")
        self.setMinimumSize(1100, 750)
        
        self.login_screen = LoginWindow()
        self.register_screen = RegisterWindow()
        self.restore_screen = RestoreWindow()
        
        self.addWidget(self.login_screen)    
        self.addWidget(self.register_screen) 
        self.addWidget(self.restore_screen)  
        
        self.setup_navigation()
        
    def setup_navigation(self):
        """Зв'язує сигнали кнопок із перемиканням індексів стека."""
        self.login_screen.on_register_click.connect(lambda: self.setCurrentIndex(1))
        self.login_screen.on_restore_click.connect(lambda: self.setCurrentIndex(2))
        
        self.register_screen.on_back_click.connect(lambda: self.setCurrentIndex(0))
        self.restore_screen.on_back_click.connect(lambda: self.setCurrentIndex(0))
        
        self.login_screen.on_login_success.connect(self.activate_main_system)

    def activate_main_system(self, username):
        """
        Створює MainWindow та запускає RTSP сервер після успішного входу.
        """
        self.main_window = MainWindow(username)
        self.addWidget(self.main_window)
        
        self.setCurrentWidget(self.main_window)
        
        self.run_rtsp_server()

    def run_rtsp_server(self):
        """Налаштовує та запускає RTSP сервер через GStreamer."""
        try:
            server = GstRtspServer.RTSPServer()
            server.set_service(config.RTSP_PORT)
            
            factory = USBRTSPFactory(config.DEFAULT_CAMERA_NAME)
            factory.set_shared(True)
            
            mounts = server.get_mount_points()
            mounts.add_factory(config.RTSP_MOUNT_POINT, factory)
            
            server.attach(None)
            print(f"[*] RTSP сервер активний: rtsp://127.0.0.1:{config.RTSP_PORT}{config.RTSP_MOUNT_POINT}")
        except Exception as e:
            print(f"[!] Помилка запуску RTSP сервера: {e}")

def main():
    app = QApplication(sys.argv)
    
    controller = PyRTSPController()
    controller.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()