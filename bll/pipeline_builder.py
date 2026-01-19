import sys
from dal.models import Camera

class PipelineBuilder:
    """
    Будує рядок запуску GStreamer.
    """

    @staticmethod
    def build(camera: Camera) -> str:
        # 1. Джерело (RTSP) + Протокол (TCP/UDP) з бази
        source = f"rtspsrc location={camera.rtsp_url} latency=0 protocols={camera.protocol}"

        # 2. Декодер (Адаптація під macOS)
        if sys.platform == "darwin":  
            # vtdec - це використання відеокарти Mac
            decoder = "rtph264depay ! h264parse ! vtdec"  
        else:
            # Для інших ОС (Windows/Linux)
            decoder = "rtph264depay ! h264parse ! avdec_h264"

        # 3. Конвертація кольору в BGR (стандарт для комп'ютерного зору)
        processing = "videoconvert ! video/x-raw,format=BGR"

        # 4. Вихід (Sink) - передача кадрів у Python
        sink = "appsink name=sink emit-signals=True sync=False max-buffers=1 drop=True"

        # Збираємо пайплайн
        return f"{source} ! {decoder} ! {processing} ! {sink}"