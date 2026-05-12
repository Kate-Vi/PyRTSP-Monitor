import pytest
from dal.repository import CameraRepository
from dal.models import Camera

def test_add_and_get_camera():
    """Тест збереження та отримання камери з БД."""
    repo = CameraRepository()
    test_cam = Camera(name="Test Cam", rtsp_url="rtsp://1.2.3.4", protocol="tcp")
    
    cam_id = repo.add(test_cam)
    assert cam_id is not None
    
    fetched_cam = repo.get_by_name("Test Cam")
    assert fetched_cam.rtsp_url == "rtsp://1.2.3.4"
    
    repo.delete(cam_id)