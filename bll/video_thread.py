import cv2
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self, camera_source=0):
        super().__init__()
        self.camera_source = camera_source
        self.running = True

    def run(self):
        # На macOS для камери використовуємо cv2.CAP_AVFOUNDATION
        cap = cv2.VideoCapture(self.camera_source)
        while self.running:
            ret, frame = cap.read()
            if ret:
                # Конвертація кольорів з BGR (OpenCV) в RGB (Qt)
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                p = convert_to_Qt_format.scaled(640, 480, aspectMode=1) # Масштабування
                self.change_pixmap_signal.emit(p)
        cap.release()

    def stop(self):
        self.running = False
        self.wait()