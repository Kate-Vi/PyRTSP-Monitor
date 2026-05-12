import pytest
from unittest.mock import MagicMock, patch
import sys

mock_gi = MagicMock()
sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = mock_gi

from bll.auth_service import AuthService

@pytest.fixture
def auth_service():
    with patch('dal.user_repository.UserRepository'), \
         patch('dal.recovery_repository.RecoveryCodeRepository'):
        service = AuthService()
        service.repo = MagicMock()
        service.recovery_repo = MagicMock()
        return service

def test_password_validation_logic(auth_service):
    """Перевірка логіки складності пароля."""
    with pytest.raises(ValueError, match="хоча б одну цифру"):
        auth_service._validate_password_strength("NoDigits!")
    with pytest.raises(ValueError, match="мінімум 8 символів"):
        auth_service._validate_password_strength("Short1!")

def test_gmail_only_validation(auth_service):
    """Перевірка обмеження реєстрації тільки для Gmail."""
    auth_service.repo.get_by_email.return_value = None
    with pytest.raises(ValueError, match="тільки пошти Gmail"):
        auth_service.register("user", "Password123!", "user@ukr.net", "I", "V")

def test_register_duplicate_username(auth_service):
    """Перевірка захисту від дублювання логінів."""
    # 1. Пошта має бути "вільною" (повертаємо None)
    auth_service.repo.get_by_email.return_value = None
    
    # 2. Логін має бути "зайнятим"
    auth_service.repo.get_by_username.return_value = {"username": "admin"}
    
    with pytest.raises(ValueError, match="Користувач з таким логіном вже існує!"):
        auth_service.register("admin", "Password123!", "admin@gmail.com", "A", "B")