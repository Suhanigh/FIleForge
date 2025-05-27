from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class TaggingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Tagging')
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Tagging feature coming soon!'))
        layout.addWidget(QPushButton('OK', clicked=self.accept)) 