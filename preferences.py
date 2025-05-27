from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QCheckBox, QPushButton

class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Preferences')
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Theme:'))
        self.theme_combo = QComboBox(); self.theme_combo.addItems(['Light', 'Dark'])
        layout.addWidget(self.theme_combo)
        layout.addWidget(QLabel('View Options:'))
        self.show_tree = QCheckBox('Show Tree View')
        self.show_details = QCheckBox('Show Details View')
        self.show_hidden = QCheckBox('Show Hidden Files')
        layout.addWidget(self.show_tree)
        layout.addWidget(self.show_details)
        layout.addWidget(self.show_hidden)
        layout.addWidget(QPushButton('OK', clicked=self.accept)) 