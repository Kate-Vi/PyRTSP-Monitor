import sys
import gi

# Налаштування GStreamer для MacOS (важливо для відео!)
try:
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
    Gst.init(None)
except ValueError:
    print("⚠️ GStreamer не знайдено або версія неправильна")
except Exception as e:
    print(f"⚠️ Помилка ініціалізації GStreamer: {e}")

from PyQt6.QtWidgets import QApplication
from ui.login_window import LoginWindow
from ui.main_window import MainWindow  # <--- Ми додали імпорт головного вікна

def main():
    app = QApplication(sys.argv)

    # Змінна, щоб вікно не зникло (Python видаляє об'єкти без посилань)
    main_window = None 

    login_window = LoginWindow()
    
    def on_login_success(username):
        nonlocal main_window 
        print(f"✅ КОРИСТУВАЧ {username} УСПІШНО УВІЙШОВ!")
        
        # 1. Закриваємо вікно входу
        login_window.close()
        
        # 2. Створюємо і показуємо Головне вікно
        try:
            main_window = MainWindow(username)
            main_window.show()
        except Exception as e:
            print(f"❌ Помилка при відкритті головного вікна: {e}")

    # Зв'язуємо сигнал успішного входу з нашою функцією
    login_window.login_successful.connect(on_login_success)
    
    login_window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()