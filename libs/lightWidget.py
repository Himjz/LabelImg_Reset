from PySide6.QtWidgets import QSpinBox
from PySide6.QtGui import QFontMetrics, QColor
from PySide6.QtCore import Qt, QSize


class LightWidget(QSpinBox):
    def __init__(self, title, parent=None):
        super(LightWidget, self).__init__(parent)
        self.setRange(0, 100)
        self.setValue(50)
        self.setSuffix(' %')
        self.setToolTip(f'{title}')
        self.setStatusTip(f'{title}')
        self.setAlignment(Qt.AlignCenter)

    def color(self):
        """返回基于当前值的叠加颜色"""
        value = self.value()
        if value < 50:
            # 变暗：减少亮度
            factor = 1.0 - (50 - value) / 50.0
            return QColor(int(0 * factor), int(0 * factor), int(0 * factor), int(255 * (1 - factor)))
        else:
            # 变亮：增加亮度
            factor = (value - 50) / 50.0
            return QColor(int(255 * factor), int(255 * factor), int(255 * factor), int(255 * factor))

    def minimumSizeHint(self):
        fm = QFontMetrics(self.font())
        # 在PySide6中使用horizontalAdvance替代width
        width = fm.horizontalAdvance(str(self.maximum()) + ' %')
        return QSize(width, super(LightWidget, self).minimumSizeHint().height())
