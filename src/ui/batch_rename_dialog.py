"""
Batch rename dialog for the File System Explorer.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QSpinBox,
    QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt
import re
import os

class BatchRenameDialog(QDialog):
    """Dialog for batch renaming files."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Rename")
        self.setMinimumWidth(400)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Pattern type selection
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("Pattern Type:"))
        self.pattern_type = QComboBox()
        self.pattern_type.addItems(["Replace", "Add Prefix", "Add Suffix", "Number Sequence"])
        self.pattern_type.currentTextChanged.connect(self._on_pattern_type_changed)
        pattern_layout.addWidget(self.pattern_type)
        layout.addLayout(pattern_layout)
        
        # Pattern input
        pattern_input_layout = QHBoxLayout()
        pattern_input_layout.addWidget(QLabel("Pattern:"))
        self.pattern_input = QLineEdit()
        pattern_input_layout.addWidget(self.pattern_input)
        layout.addLayout(pattern_input_layout)
        
        # Number sequence options
        self.number_options = QHBoxLayout()
        self.number_options.addWidget(QLabel("Start:"))
        self.start_number = QSpinBox()
        self.start_number.setRange(1, 9999)
        self.number_options.addWidget(self.start_number)
        
        self.number_options.addWidget(QLabel("Step:"))
        self.step_number = QSpinBox()
        self.step_number.setRange(1, 100)
        self.number_options.addWidget(self.step_number)
        
        self.number_options.addWidget(QLabel("Digits:"))
        self.digits_number = QSpinBox()
        self.digits_number.setRange(1, 5)
        self.digits_number.setValue(2)
        self.number_options.addWidget(self.digits_number)
        layout.addLayout(self.number_options)
        
        # Options
        options_layout = QHBoxLayout()
        self.case_sensitive = QCheckBox("Case Sensitive")
        options_layout.addWidget(self.case_sensitive)
        
        self.keep_extension = QCheckBox("Keep Extension")
        self.keep_extension.setChecked(True)
        options_layout.addWidget(self.keep_extension)
        layout.addLayout(options_layout)
        
        # Preview
        layout.addWidget(QLabel("Preview:"))
        self.preview_text = QLineEdit()
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.preview_button = QPushButton("Preview")
        self.preview_button.clicked.connect(self._preview_rename)
        button_layout.addWidget(self.preview_button)
        
        self.rename_button = QPushButton("Rename")
        self.rename_button.clicked.connect(self.accept)
        button_layout.addWidget(self.rename_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # Initialize visibility
        self._on_pattern_type_changed(self.pattern_type.currentText())
    
    def _on_pattern_type_changed(self, pattern_type):
        """Handle pattern type changes."""
        self.pattern_input.setEnabled(pattern_type != "Number Sequence")
        self.start_number.setEnabled(pattern_type == "Number Sequence")
        self.step_number.setEnabled(pattern_type == "Number Sequence")
        self.digits_number.setEnabled(pattern_type == "Number Sequence")
    
    def _preview_rename(self):
        """Show preview of the rename operation."""
        pattern = self.pattern_input.text()
        if not pattern and self.pattern_type.currentText() != "Number Sequence":
            QMessageBox.warning(self, "Error", "Please enter a pattern")
            return
        
        # Example preview
        example = "example.txt"
        new_name = self._apply_rename_pattern(example)
        self.preview_text.setText(f"{example} → {new_name}")
    
    def _apply_rename_pattern(self, filename):
        """Apply the rename pattern to a filename."""
        name, ext = os.path.splitext(filename)
        pattern_type = self.pattern_type.currentText()
        pattern = self.pattern_input.text()
        
        if pattern_type == "Replace":
            if self.case_sensitive.isChecked():
                new_name = name.replace(pattern, "")
            else:
                new_name = re.sub(pattern, "", name, flags=re.IGNORECASE)
        
        elif pattern_type == "Add Prefix":
            new_name = pattern + name
        
        elif pattern_type == "Add Suffix":
            new_name = name + pattern
        
        elif pattern_type == "Number Sequence":
            # This is just a preview, actual numbering will be done during rename
            new_name = name + "_01"
        
        if self.keep_extension.isChecked():
            new_name += ext
        
        return new_name
    
    def get_rename_options(self):
        """Get the rename options."""
        return {
            'pattern_type': self.pattern_type.currentText(),
            'pattern': self.pattern_input.text(),
            'case_sensitive': self.case_sensitive.isChecked(),
            'keep_extension': self.keep_extension.isChecked(),
            'start_number': self.start_number.value(),
            'step_number': self.step_number.value(),
            'digits': self.digits_number.value()
        } 