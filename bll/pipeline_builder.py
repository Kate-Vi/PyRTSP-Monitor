import sys
from dal.models import Camera

class PipelineBuilder:
    """
    Будує рядок запуску GStreamer.
    """

    @staticmethod
    def build(camera: Camera) -> str:
        # --- ТЕСТОВИЙ РЕЖИМ ---
        if camera.rtsp_url == "0" or camera.rtsp_url == "test":
            return (
                "videotestsrc pattern=ball ! "
                "videoconvert ! "
                "video/x-raw,format=BGR ! "
                "appsink name=sink emit-signals=True sync=False max-buffers=1 drop=True"
            )

        # --- РЕАЛЬНА КАМЕРА ---
        # 1. Джерело (RTSP)
        # latency=0 робить відео максимально "живим"
        source = f"rtspsrc location={camera.rtsp_url} latency=0 protocols={camera.protocol}"

        # 2. Декодер
        # 👇 ЗМІНА: Використовуємо avdec_h264 для ВСІХ систем (він надійніший)
        decoder = "rtph264depay ! h264parse ! avdec_h264"

        # 3. Обробка
        processing = "videoconvert ! video/x-raw,format=BGR"

        # 4. Вихід
        sink = "appsink name=sink emit-signals=True sync=False max-buffers=1 drop=True"

        return f"{source} ! {decoder} ! {processing} ! {sink}"