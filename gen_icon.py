import os
import sys

os.makedirs('assets', exist_ok=True)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QColor, QPainter, QFont
from PySide6.QtCore import Qt, QRect

app = QApplication(sys.argv)

pixmap = QPixmap(256, 256)
pixmap.fill(Qt.GlobalColor.transparent)

painter = QPainter(pixmap)
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
painter.setBrush(QColor('#2980b9'))
painter.setPen(Qt.PenStyle.NoPen)
painter.drawEllipse(4, 4, 248, 248)

font = QFont('Arial Black', 100)
font.setBold(True)
painter.setFont(font)
painter.setPen(QColor('white'))
painter.drawText(QRect(0, 0, 256, 256), Qt.AlignmentFlag.AlignCenter, 'W')
painter.end()

pixmap.save('assets/icon.ico')
print('Icon generated.')
app.quit()
