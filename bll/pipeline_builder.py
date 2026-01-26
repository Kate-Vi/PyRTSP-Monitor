import sys
from dal.models import Camera

class PipelineBuilder:
    """
    Будує GStreamer пайплайн.
    ВЕРСІЯ: Оптимізована (Downscaling + FPS Limit + Queues)
    """

    @staticmethod
    def build(camera: Camera) -> str:
        # --- 1. ТЕСТОВИЙ РЕЖИМ ---
        # Навіть для тестів ми ріжемо якість, щоб не навантажувати процесор
        if camera.rtsp_url == "0" or camera.rtsp_url == "test":
            return (
                "videotestsrc pattern=ball ! "
                "video/x-raw,width=480,height=320,framerate=15/1 ! "  # <--- ОПТИМІЗАЦІЯ
                "videoconvert ! "
                "video/x-raw,format=BGR ! "
                "appsink name=sink emit-signals=True sync=False max-buffers=1 drop=True"
            )

        # --- 2. РЕАЛЬНА КАМЕРА ---
        
        # [Джерело]
        # latency=200: буфер 200мс для компенсації лагів мережі
        # drop-on-latency: викидаємо старі пакети, якщо CPU не стягує (захист від зависання)
        source = (
            f"rtspsrc location={camera.rtsp_url} "
            f"latency=200 drop-on-latency=true protocols=tcp"  # <--- ЗАХИСТ ВІД ЛАГІВ
        )

        # [Декодер]
        # queue: створює окремий потік (Thread) для декодування.
        # Це дозволяє декодеру працювати, навіть якщо ресайз (наступний крок) зайнятий.
        decoder = (
            "rtph264depay ! h264parse ! "
            "queue max-size-buffers=3 ! "  # <--- БАГАТОПОТОКОВІСТЬ
            "avdec_h264"
        )

        # [Оптимізація - СЕРЦЕ ФІКСУ]
        # Ми перетворюємо потік 1920x1080 (6MB/кадр) -> 480x320 (0.4MB/кадр)
        # Це зменшує навантаження на RAM і Python у ~15 разів.
        optimization = (
            "queue ! "                                       # <--- Ще один буфер
            "videoscale ! video/x-raw,width=480,height=320 ! " # <--- DOWNSCALING
            "videorate ! video/x-raw,framerate=15/1"         # <--- FPS LIMIT (було 30/60 -> стало 15)
        )

        # [Конвертація кольору]
        # Перетворення YUV -> BGR (для OpenCV/Qt)
        converter = "queue ! videoconvert ! video/x-raw,format=BGR"

        # [Вихід в Python]
        # max-buffers=1: Тримаємо в пам'яті тільки ОДИН останній кадр.
        # drop=True: Якщо GUI не встиг забрати кадр, він перезаписується новим.
        sink = "appsink name=sink emit-signals=True sync=False max-buffers=1 drop=True"

        # Збираємо конструктор Lego
        pipeline_str = f"{source} ! {decoder} ! {optimization} ! {converter} ! {sink}"
        
        return pipeline_str