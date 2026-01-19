import sys
from PyQt6.QtWidgets import QApplication
from ui.login_window import LoginWindow

def main():
    # 1. Створюємо об'єкт додатку (обов'язково для PyQt)
    app = QApplication(sys.argv)

    # 2. Створюємо вікно логіну
    login_window = LoginWindow()
    
    # 3. Визначаємо функцію, яка спрацює, коли користувач успішно зайде
    def on_login_success(username):
        print(f"✅ КОРИСТУВАЧ {username} УСПІШНО УВІЙШОВ!")
        print("Тут ми пізніше відкриємо головне вікно з камерами.")
        
        # Закриваємо вікно логіну
        login_window.close()
        
        # TODO: На наступному етапі тут буде:
        # main_window = MainWindow(username)
        # main_window.show()

    # Підписуємося на сигнал (аналог += event в C#)
    login_window.login_successful.connect(on_login_success)

    # 4. Показуємо вікно
    login_window.show()

    # 5. Запускаємо цикл обробки подій
    sys.exit(app.exec())

if __name__ == "__main__":
    main()