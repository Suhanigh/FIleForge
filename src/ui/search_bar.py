"""
Search bar implementation for the File System Explorer.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton,
    QComboBox, QLabel, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

class SearchBar(QWidget):
    """Search bar widget with advanced search options."""
    
    # Signal emitted when search is triggered
    search_triggered = Signal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the search bar UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files...")
        self.search_input.returnPressed.connect(self._on_search)
        layout.addWidget(self.search_input)
        
        # Search type selector
        self.search_type = QComboBox()
        self.search_type.addItems(["Name", "Content", "Tags"])
        layout.addWidget(self.search_type)
        
        # Case sensitivity option
        self.case_sensitive = QCheckBox("Case Sensitive")
        layout.addWidget(self.case_sensitive)
        
        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._on_search)
        layout.addWidget(self.search_button)
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._clear_search)
        layout.addWidget(self.clear_button)
    
    def _on_search(self):
        """Handle search button click or enter key press."""
        search_text = self.search_input.text().strip()
        if not search_text:
            return
        
        search_options = {
            'type': self.search_type.currentText().lower(),
            'case_sensitive': self.case_sensitive.isChecked()
        }
        
        self.search_triggered.emit(search_text, search_options)
    
    def _clear_search(self):
        """Clear the search input and reset options."""
        self.search_input.clear()
        self.search_type.setCurrentIndex(0)
        self.case_sensitive.setChecked(False)
        self.search_triggered.emit("", {})
    
    def get_search_text(self):
        """Get the current search text."""
        return self.search_input.text().strip()
    
    def get_search_options(self):
        """Get the current search options."""
        return {
            'type': self.search_type.currentText().lower(),
            'case_sensitive': self.case_sensitive.isChecked()
        } 