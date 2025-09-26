from PySide6.QtCore import QSize
from PySide6.QtWidgets import QSpinBox
from PySide6.QtGui import QFontMetrics, Qt


class ZoomWidget(QSpinBox):
    def __init__(self, parent=None):
        super(ZoomWidget, self).__init__(parent)
        self.setRange(10, 500)
        self.setSuffix(' %')
        self.setValue(100)
        self.setToolTip('缩放百分比')
        self.setStatusTip('缩放百分比')
        self.setAlignment(Qt.AlignCenter)

    def minimumSizeHint(self):
        fm = QFontMetrics(self.font())
        # 在PySide6中使用horizontalAdvance替代width
        width = fm.horizontalAdvance(str(self.maximum()) + ' %')
        return QSize(width, super(ZoomWidget, self).minimumSizeHint().height())
