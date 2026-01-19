from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QBrush
from PyQt6.QtCore import Qt

class PasswordEdit(QLineEdit):
    """
    Кастомний віджет для введення пароля, успадкований від QLineEdit.
    
    Особливості:
    1. Має вбудовану кнопку (Action) у правій частині поля.
    2. Дозволяє перемикати видимість пароля (зірочки <-> текст).
    3. Використовує програмне малювання іконки (QPainter), що робить віджет 
       незалежним від зовнішніх файлів зображень (.png, .ico).
    """

    def __init__(self, parent=None):
        """
        Ініціалізація віджета.
        Налаштовує режим пароля, створює іконки та додає кнопку керування.
        """
        super().__init__(parent)
        
        # Встановлюємо режим "Password" (відображення зірочок) за замовчуванням
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self.setPlaceholderText("******")
        
        # Колір для малювання іконок (сірий #888888 - нейтральний)
        self.icon_color = "#888888"
        
        # Генеруємо дві версії іконки програмно:
        # 1. icon_show - звичайне око (пароль прихований, натисни щоб побачити)
        # 2. icon_hide - перекреслене око (пароль видно, натисни щоб сховати)
        self.icon_show = self._draw_eye_icon(visible=True)
        self.icon_hide = self._draw_eye_icon(visible=False)

        # Додаємо інтерактивну іконку в кінець поля (TrailingPosition)
        self.toggle_action = self.addAction(
            self.icon_show, 
            QLineEdit.ActionPosition.TrailingPosition
        )
        
        # Підключаємо обробник натискання на іконку
        self.toggle_action.triggered.connect(self.toggle_password_visibility)
        
        # Прапорець поточного стану (False = пароль прихований)
        self.is_password_shown = False

    def toggle_password_visibility(self):
        """
        Перемикає режим відображення пароля при натисканні на око.
        Змінює EchoMode та іконку.
        """
        if self.is_password_shown:
            # Якщо пароль зараз видно -> ХОВАЄМО його
            self.setEchoMode(QLineEdit.EchoMode.Password)
            # Ставимо іконку "Око" (підказка: "натисни, щоб підглянути")
            self.toggle_action.setIcon(self.icon_show)
            self.is_password_shown = False
        else:
            # Якщо пароль прихований -> ПОКАЗУЄМО його
            self.setEchoMode(QLineEdit.EchoMode.Normal)
            # Ставимо іконку "Перекреслене око" (підказка: "натисни, щоб сховати")
            self.toggle_action.setIcon(self.icon_hide)
            self.is_password_shown = True

    def _draw_eye_icon(self, visible: bool) -> QIcon:
        """
        Внутрішній метод для програмного малювання векторної іконки ока.
        
        Args:
            visible (bool): 
                True - малює звичайне око (символ "показати").
                False - малює перекреслене око (символ "сховати").
        
        Returns:
            QIcon: Готова іконка для використання в інтерфейсі.
        """
        size = 24  # Розмір іконки в пікселях
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent) # Прозорий фон
        
        painter = QPainter(pixmap)
        # Вмикаємо згладжування (Antialiasing), щоб лінії були рівними, без "сходинок"
        painter.setRenderHint(QPainter.RenderHint.Antialiasing) 
        
        # Налаштування "олівця" (контур фігур)
        pen = QPen(QColor(self.icon_color))
        pen.setWidth(2) # Товщина ліній
        painter.setPen(pen)
        
        # 1. Малюємо контур ока (еліпс)
        # drawEllipse(x, y, width, height)
        painter.drawEllipse(2, 6, 20, 12)
        
        # 2. Малюємо зіницю (зафарбоване коло по центру)
        painter.setBrush(QBrush(QColor(self.icon_color))) # Заливка тим же кольором
        painter.drawEllipse(9, 9, 6, 6)
        
        # 3. Якщо потрібна іконка "Сховати" (visible=False), додаємо лінію перекреслення
        if not visible:
            # Малюємо діагональну лінію поверх ока
            painter.drawLine(4, 20, 20, 4) 
            
        painter.end() # Завершуємо малювання
        
        return QIcon(pixmap)