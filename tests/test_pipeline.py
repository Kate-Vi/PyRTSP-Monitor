import pytest
from unittest.mock import MagicMock
import sys

# КРИТИЧНО: Заглушка для GStreamer перед імпортом нашого коду
mock_gi = MagicMock()
sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = mock_gi

from bll.pipeline_builder import PipelineBuilder

def test_pipeline_latency_logic():
    """Перевірка вибору затримки (latency) залежно від URL."""
    
    # Створюємо фейкові об'єкти камер
    local_cam = MagicMock()
    local_cam.rtsp_url = "rtsp://192.168.1.10"
    
    wan_cam = MagicMock()
    wan_cam.rtsp_url = "rtsp://8.8.8.8/stream"
    
    # Перевіряємо локальну мережу (latency=100)
    local_pipe = PipelineBuilder.build(local_cam)
    assert "latency=100" in local_pipe
    
    # Перевіряємо зовнішню мережу (latency=2000)
    wan_pipe = PipelineBuilder.build(wan_cam)
    assert "latency=2000" in wan_pipe

def test_mac_camera_index():
    """Перевірка визначення індексу вбудованої камери."""
    idx = PipelineBuilder._resolve_device_index("built-in")
    assert idx == 0
    
    idx_iphone = PipelineBuilder._resolve_device_index("iphone")
    assert idx_iphone == 1