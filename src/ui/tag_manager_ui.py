"""
Tag management UI component for the File System Explorer.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QLineEdit, QLabel, QMessageBox,
    QInputDialog, QMenu
)
from PySide6.QtCore import Qt, Signal
from utils.tag_manager import TagManager

class TagManagerUI(QWidget):
    """UI component for managing file tags."""
    
    # Signal emitted when tags are modified
    tags_modified = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tag_manager = TagManager()
        self._init_ui()
        self._load_tags()
    
    def _init_ui(self):
        """Initialize the tag management UI components."""
        layout = QVBoxLayout(self)
        
        # Tag list
        self.tag_list = QListWidget()
        self.tag_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tag_list.customContextMenuRequested.connect(self._show_tag_context_menu)
        layout.addWidget(QLabel("Tags:"))
        layout.addWidget(self.tag_list)
        
        # Add tag section
        add_layout = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Enter new tag...")
        self.tag_input.returnPressed.connect(self._add_tag)
        add_layout.addWidget(self.tag_input)
        
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self._add_tag)
        add_layout.addWidget(self.add_button)
        layout.addLayout(add_layout)
        
        # Tag statistics
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)
        
        # Update statistics
        self._update_stats()
    
    def _load_tags(self):
        """Load tags into the list widget."""
        self.tag_list.clear()
        for tag in self.tag_manager.get_all_tags():
            self.tag_list.addItem(tag)
    
    def _update_stats(self):
        """Update tag statistics display."""
        stats = self.tag_manager.get_tag_stats()
        if stats:
            stats_text = "Tag Statistics:\n"
            for tag, count in stats.items():
                stats_text += f"{tag}: {count} files\n"
            self.stats_label.setText(stats_text)
        else:
            self.stats_label.setText("No tags available")
    
    def _add_tag(self):
        """Add a new tag."""
        tag = self.tag_input.text().strip()
        if not tag:
            return
        
        if tag in self.tag_manager.get_all_tags():
            QMessageBox.warning(self, "Warning", f"Tag '{tag}' already exists!")
            return
        
        # Add tag to manager
        self.tag_manager.tags[tag] = set()
        self.tag_manager._save_tags()
        
        # Update UI
        self.tag_list.addItem(tag)
        self.tag_input.clear()
        self._update_stats()
        self.tags_modified.emit()
    
    def _show_tag_context_menu(self, position):
        """Show context menu for tag operations."""
        item = self.tag_list.itemAt(position)
        if not item:
            return
        
        tag = item.text()
        menu = QMenu()
        
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        
        action = menu.exec(self.tag_list.mapToGlobal(position))
        
        if action == rename_action:
            self._rename_tag(tag)
        elif action == delete_action:
            self._delete_tag(tag)
    
    def _rename_tag(self, old_tag):
        """Rename a tag."""
        new_tag, ok = QInputDialog.getText(
            self, "Rename Tag",
            f"Enter new name for tag '{old_tag}':",
            text=old_tag
        )
        
        if ok and new_tag and new_tag != old_tag:
            if self.tag_manager.rename_tag(old_tag, new_tag):
                # Update UI
                items = self.tag_list.findItems(old_tag, Qt.MatchFlag.MatchExactly)
                if items:
                    items[0].setText(new_tag)
                self._update_stats()
                self.tags_modified.emit()
            else:
                QMessageBox.warning(self, "Error", "Failed to rename tag!")
    
    def _delete_tag(self, tag):
        """Delete a tag."""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the tag '{tag}'?\n"
            "This will remove the tag from all files.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove tag from all files
            for file_path in self.tag_manager.get_tagged_files(tag):
                self.tag_manager.remove_tag(file_path, tag)
            
            # Update UI
            items = self.tag_list.findItems(tag, Qt.MatchFlag.MatchExactly)
            if items:
                self.tag_list.takeItem(self.tag_list.row(items[0]))
            self._update_stats()
            self.tags_modified.emit()
    
    def add_tag_to_file(self, file_path: str, tag: str) -> bool:
        """
        Add a tag to a file.
        
        Args:
            file_path: Path to the file
            tag: Tag to add
            
        Returns:
            True if successful, False otherwise
        """
        if self.tag_manager.add_tag(file_path, tag):
            self._update_stats()
            self.tags_modified.emit()
            return True
        return False
    
    def remove_tag_from_file(self, file_path: str, tag: str) -> bool:
        """
        Remove a tag from a file.
        
        Args:
            file_path: Path to the file
            tag: Tag to remove
            
        Returns:
            True if successful, False otherwise
        """
        if self.tag_manager.remove_tag(file_path, tag):
            self._update_stats()
            self.tags_modified.emit()
            return True
        return False
    
    def get_file_tags(self, file_path: str) -> set:
        """
        Get all tags for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Set of tags
        """
        return self.tag_manager.get_file_tags(file_path)
    
    def get_tagged_files(self, tag: str) -> set:
        """
        Get all files with a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            Set of file paths
        """
        return self.tag_manager.get_tagged_files(tag) 