"""
UI customization module for the File System Explorer.
"""

import json
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QLabel, QPushButton, QCheckBox, QGroupBox,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette, QColor

class UICustomizer(QWidget):
    """UI customization widget for managing themes and layout preferences."""
    
    # Signal emitted when theme changes
    theme_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preferences_file = os.path.expanduser("~/.file_explorer_preferences.json")
        self.current_theme = "light"
        self._init_ui()
        self._load_preferences()
    
    def _init_ui(self):
        """Initialize the UI customizer components."""
        layout = QVBoxLayout(self)
        
        # Theme selection
        theme_group = QGroupBox("Theme")
        theme_layout = QHBoxLayout()
        
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Light", "Dark", "System"])
        self.theme_selector.currentTextChanged.connect(self._on_theme_changed)
        theme_layout.addWidget(QLabel("Theme:"))
        theme_layout.addWidget(self.theme_selector)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # View options
        view_group = QGroupBox("View Options")
        view_layout = QVBoxLayout()
        
        self.tree_view_checkbox = QCheckBox("Show Tree View")
        self.tree_view_checkbox.setChecked(True)
        view_layout.addWidget(self.tree_view_checkbox)
        
        self.details_view_checkbox = QCheckBox("Show Details View")
        self.details_view_checkbox.setChecked(True)
        view_layout.addWidget(self.details_view_checkbox)
        
        view_group.setLayout(view_layout)
        layout.addWidget(view_group)
        
        # Export directory option
        export_group = QGroupBox("Export/Save Directory")
        export_layout = QHBoxLayout()
        self.export_dir_label = QLabel("Not set")
        self.export_dir_button = QPushButton("Choose...")
        self.export_dir_button.clicked.connect(self._choose_export_dir)
        export_layout.addWidget(self.export_dir_label)
        export_layout.addWidget(self.export_dir_button)
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        # Save button
        self.save_button = QPushButton("Save Preferences")
        self.save_button.clicked.connect(self._save_preferences)
        layout.addWidget(self.save_button)
        
        layout.addStretch()
    
    def _load_preferences(self):
        """Load user preferences from file."""
        try:
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r') as f:
                    prefs = json.load(f)
                    
                # Apply theme
                theme = prefs.get('theme', 'light')
                self.theme_selector.setCurrentText(theme.capitalize())
                self._apply_theme(theme)
                
                # Apply view options
                self.tree_view_checkbox.setChecked(prefs.get('show_tree_view', True))
                self.details_view_checkbox.setChecked(prefs.get('show_details_view', True))
                
                # Apply export directory
                self.export_dir = prefs.get('export_dir', '')
                self.export_dir_label.setText(self.export_dir if self.export_dir else "Not set")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load preferences: {str(e)}")
    
    def _save_preferences(self):
        """Save user preferences to file."""
        try:
            prefs = {
                'theme': self.current_theme,
                'show_tree_view': self.tree_view_checkbox.isChecked(),
                'show_details_view': self.details_view_checkbox.isChecked(),
                'export_dir': getattr(self, 'export_dir', '')
            }
            
            with open(self.preferences_file, 'w') as f:
                json.dump(prefs, f, indent=4)
            
            QMessageBox.information(self, "Success", "Preferences saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save preferences: {str(e)}")
    
    def _on_theme_changed(self, theme):
        """Handle theme change."""
        theme = theme.lower()
        self.current_theme = theme
        self._apply_theme(theme)
        self.theme_changed.emit(theme)
    
    def _is_system_dark_mode(self):
        """Check if system is in dark mode."""
        app = QApplication.instance()
        if app is None:
            return False
        
        # Get system palette
        system_palette = app.style().standardPalette()
        window_color = system_palette.color(QPalette.ColorRole.Window)
        
        # Calculate relative luminance
        luminance = (0.299 * window_color.red() + 0.587 * window_color.green() + 0.114 * window_color.blue()) / 255
        
        # Return True if dark mode (luminance < 0.5)
        return luminance < 0.5
    
    def _apply_theme(self, theme):
        """Apply the selected theme."""
        palette = QPalette()
        
        # Handle system theme
        if theme == "system":
            theme = "dark" if self._is_system_dark_mode() else "light"
        
        if theme == "dark":
            # Dark theme colors
            palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
            
            # Additional dark theme colors
            palette.setColor(QPalette.ColorRole.Mid, QColor(80, 80, 80))
            palette.setColor(QPalette.ColorRole.Dark, QColor(100, 100, 100))
            palette.setColor(QPalette.ColorRole.Shadow, QColor(20, 20, 20))
        else:
            # Light theme colors (default)
            palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
            palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(233, 233, 233))
            palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.black)
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
            palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
            palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
            palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
            
            # Additional light theme colors
            palette.setColor(QPalette.ColorRole.Mid, QColor(200, 200, 200))
            palette.setColor(QPalette.ColorRole.Dark, QColor(160, 160, 160))
            palette.setColor(QPalette.ColorRole.Shadow, QColor(100, 100, 100))
        
        # Apply palette to application
        app = QApplication.instance()
        if app is not None:
            app.setPalette(palette)
    
    def _choose_export_dir(self):
        from PySide6.QtWidgets import QFileDialog
        dir_ = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if dir_:
            self.export_dir_label.setText(dir_)
            self.export_dir = dir_
    
    def get_preferences(self):
        """Get current preferences."""
        return {
            'theme': self.current_theme,
            'show_tree_view': self.tree_view_checkbox.isChecked(),
            'show_details_view': self.details_view_checkbox.isChecked(),
            'export_dir': getattr(self, 'export_dir', '')
        } 