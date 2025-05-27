from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class SearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Search')
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Search feature coming soon!'))
        layout.addWidget(QPushButton('OK', clicked=self.accept)) 