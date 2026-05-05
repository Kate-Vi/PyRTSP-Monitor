import gi

try:
    gi.require_version('Gst', '1.0')
    gi.require_version('GstRtspServer', '1.0')
    from gi.repository import Gst, GstRtspServer
except Exception as e:
    print(f"Помилка GStreamer: {e}")


# Префікси локальних мереж для визначення LAN vs WAN
_LOCAL_PREFIXES = (
    "rtsp://127.", "rtsp://localhost",
    "rtsp://192.168.", "rtsp://10.",
    "rtsp://172.16.", "rtsp://172.17.", "rtsp://172.18.", "rtsp://172.19.",
    "rtsp://172.2", "rtsp://172.3",
)


class PipelineBuilder:
    @staticmethod
    def build(camera):
        url = camera.rtsp_url.strip() if hasattr(camera, 'rtsp_url') else ""
        url_lower = url.lower()

        # --- 1. RTSP ПОТОКИ (rtsp://...) ---
        if url_lower.startswith("rtsp://"):
            is_local = any(url_lower.startswith(p) for p in _LOCAL_PREFIXES)
            # LAN: 100ms — майже без затримки
            # WAN: 2000ms — буфер для нестабільного інтернет-стріму
            latency = 100 if is_local else 2000
            print(f"[*] RTSP {'LAN' if is_local else 'WAN'} (latency={latency}ms): {url}")

            # decodebin автоматично визначає кодек: H.264, H.265, MPEG4 тощо
            return (
                f"rtspsrc location={url} protocols=tcp latency={latency} "
                "buffer-mode=auto drop-on-latency=true ! "
                "decodebin ! "
                "videoconvert ! videoscale ! "
                "video/x-raw,width=640,height=360 ! "
                "videoconvert ! video/x-raw,format=BGR ! "
                "appsink name=sink emit-signals=true sync=false max-buffers=2 drop=true"
            )

        # --- 2. ЛОКАЛЬНІ КАМЕРИ macOS (avfvideosrc) ---
        device_index = PipelineBuilder._resolve_device_index(url)
        print(f"[*] Локальна AVFoundation камера (device-index={device_index}): '{url}'")

        return (
            f"avfvideosrc device-index={device_index} ! "
            "queue max-size-buffers=2 leaky=downstream ! "
            "videoconvert ! videoscale ! "
            "video/x-raw,width=640,height=360,framerate=30/1 ! "
            "videoconvert ! video/x-raw,format=BGR ! "
            "appsink name=sink emit-signals=true sync=false drop=true max-buffers=1"
        )

    @staticmethod
    def _resolve_device_index(url: str) -> int:
        """
        Визначає device-index для avfvideosrc:
          "0", "" або "built-in" -> 0 (вбудована MacBook)
          "1" або "iphone"       -> 1 (iPhone Continuity / USB)
          будь-яке ціле число    -> те число
        """
        s = url.lower().strip()
        if s in ("", "0", "built-in", "macbook", "laptop"):
            return 0
        if "iphone" in s or s == "1":
            return 1
        try:
            return int(s)
        except ValueError:
            return 0


class USBRTSPFactory(GstRtspServer.RTSPMediaFactory):
    """
    Фабрика для трансляції вбудованої/USB камери MacBook
    через локальний RTSP сервер (для перегляду ззовні).
    """
    def __init__(self, camera_name: str):
        GstRtspServer.RTSPMediaFactory.__init__(self)
        self.camera_name = camera_name

    def do_create_element(self, url):
        pipeline_str = (
            "avfvideosrc device-index=0 ! "
            "videoconvert ! "
            "video/x-raw,format=I420,width=1280,height=720,framerate=30/1 ! "
            "x264enc tune=zerolatency speed-preset=ultrafast key-int-max=30 ! "
            "rtph264pay name=pay0 pt=96 config-interval=1"
        )
        print(f"[RTSP Factory] Трансляція камери: {self.camera_name}")
        return Gst.parse_launch(pipeline_str)