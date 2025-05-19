"""
File permissions dialog for the File System Explorer.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QPushButton, QGroupBox, QLineEdit,
    QMessageBox
)
from PySide6.QtCore import Qt
import os
import stat

class PermissionsDialog(QDialog):
    """Dialog for managing file permissions."""
    
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setWindowTitle("File Permissions")
        self.setMinimumWidth(400)
        self._init_ui()
        self._load_current_permissions()
    
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # File path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("File:"))
        self.path_label = QLineEdit(self.file_path)
        self.path_label.setReadOnly(True)
        path_layout.addWidget(self.path_label)
        layout.addLayout(path_layout)
        
        # Owner permissions
        owner_group = QGroupBox("Owner")
        owner_layout = QVBoxLayout()
        
        self.owner_read = QCheckBox("Read")
        self.owner_write = QCheckBox("Write")
        self.owner_execute = QCheckBox("Execute")
        
        owner_layout.addWidget(self.owner_read)
        owner_layout.addWidget(self.owner_write)
        owner_layout.addWidget(self.owner_execute)
        owner_group.setLayout(owner_layout)
        layout.addWidget(owner_group)
        
        # Group permissions
        group_group = QGroupBox("Group")
        group_layout = QVBoxLayout()
        
        self.group_read = QCheckBox("Read")
        self.group_write = QCheckBox("Write")
        self.group_execute = QCheckBox("Execute")
        
        group_layout.addWidget(self.group_read)
        group_layout.addWidget(self.group_write)
        group_layout.addWidget(self.group_execute)
        group_group.setLayout(group_layout)
        layout.addWidget(group_group)
        
        # Others permissions
        others_group = QGroupBox("Others")
        others_layout = QVBoxLayout()
        
        self.others_read = QCheckBox("Read")
        self.others_write = QCheckBox("Write")
        self.others_execute = QCheckBox("Execute")
        
        others_layout.addWidget(self.others_read)
        others_layout.addWidget(self.others_write)
        others_layout.addWidget(self.others_execute)
        others_group.setLayout(others_layout)
        layout.addWidget(others_group)
        
        # Numeric mode
        numeric_group = QGroupBox("Numeric Mode")
        numeric_layout = QHBoxLayout()
        
        numeric_layout.addWidget(QLabel("Mode:"))
        self.numeric_mode = QLineEdit()
        self.numeric_mode.setReadOnly(True)
        numeric_layout.addWidget(self.numeric_mode)
        
        numeric_group.setLayout(numeric_layout)
        layout.addWidget(numeric_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self._apply_permissions)
        button_layout.addWidget(self.apply_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self._connect_permission_signals()
    
    def _connect_permission_signals(self):
        """Connect signals for permission changes."""
        checkboxes = [
            self.owner_read, self.owner_write, self.owner_execute,
            self.group_read, self.group_write, self.group_execute,
            self.others_read, self.others_write, self.others_execute
        ]
        
        for checkbox in checkboxes:
            checkbox.stateChanged.connect(self._update_numeric_mode)
    
    def _load_current_permissions(self):
        """Load current file permissions."""
        try:
            st = os.stat(self.file_path)
            mode = st.st_mode
            
            # Set owner permissions
            self.owner_read.setChecked(bool(mode & stat.S_IRUSR))
            self.owner_write.setChecked(bool(mode & stat.S_IWUSR))
            self.owner_execute.setChecked(bool(mode & stat.S_IXUSR))
            
            # Set group permissions
            self.group_read.setChecked(bool(mode & stat.S_IRGRP))
            self.group_write.setChecked(bool(mode & stat.S_IWGRP))
            self.group_execute.setChecked(bool(mode & stat.S_IXGRP))
            
            # Set others permissions
            self.others_read.setChecked(bool(mode & stat.S_IROTH))
            self.others_write.setChecked(bool(mode & stat.S_IWOTH))
            self.others_execute.setChecked(bool(mode & stat.S_IXOTH))
            
            # Update numeric mode
            self._update_numeric_mode()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load permissions: {str(e)}")
    
    def _update_numeric_mode(self):
        """Update the numeric mode display."""
        mode = 0
        
        # Owner permissions
        if self.owner_read.isChecked():
            mode |= stat.S_IRUSR
        if self.owner_write.isChecked():
            mode |= stat.S_IWUSR
        if self.owner_execute.isChecked():
            mode |= stat.S_IXUSR
        
        # Group permissions
        if self.group_read.isChecked():
            mode |= stat.S_IRGRP
        if self.group_write.isChecked():
            mode |= stat.S_IWGRP
        if self.group_execute.isChecked():
            mode |= stat.S_IXGRP
        
        # Others permissions
        if self.others_read.isChecked():
            mode |= stat.S_IROTH
        if self.others_write.isChecked():
            mode |= stat.S_IWOTH
        if self.others_execute.isChecked():
            mode |= stat.S_IXOTH
        
        # Update display
        self.numeric_mode.setText(f"{mode:04o}")
    
    def _apply_permissions(self):
        """Apply the selected permissions to the file."""
        try:
            mode = int(self.numeric_mode.text(), 8)
            os.chmod(self.file_path, mode)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply permissions: {str(e)}")
    
    def _apply_theme_styles(self, is_dark):
        """Apply theme-specific styles."""
        if is_dark:
            self.setStyleSheet("""
                QDialog {
                    background-color: #353535;
                    color: white;
                }
                QGroupBox {
                    border: 1px solid #404040;
                    border-radius: 4px;
                    margin-top: 1em;
                    padding-top: 1em;
                    color: white;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px;
                }
                QCheckBox {
                    color: white;
                }
                QLineEdit {
                    background-color: #2d2d2d;
                    color: white;
                    border: 1px solid #404040;
                    border-radius: 4px;
                }
                QPushButton {
                    background-color: #404040;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: white;
                    color: black;
                }
                QGroupBox {
                    border: 1px solid #dcdcdc;
                    border-radius: 4px;
                    margin-top: 1em;
                    padding-top: 1em;
                    color: black;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px;
                }
                QCheckBox {
                    color: black;
                }
                QLineEdit {
                    background-color: #f5f5f5;
                    color: black;
                    border: 1px solid #dcdcdc;
                    border-radius: 4px;
                }
                QPushButton {
                    background-color: #e0e0e0;
                    color: black;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
            """) 