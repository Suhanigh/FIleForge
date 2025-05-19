"""
Tag management system for the File System Explorer.
"""

import json
import os
from typing import List, Dict, Set, Optional
from datetime import datetime

class TagManager:
    """Class managing file tags and tag-based operations."""
    
    def __init__(self, tags_file: str = None):
        """
        Initialize the tag manager.
        
        Args:
            tags_file: Path to the tags database file
        """
        self.tags_file = tags_file or os.path.expanduser("~/.file_explorer_tags.json")
        self.tags: Dict[str, Set[str]] = {}  # tag -> set of file paths
        self.file_tags: Dict[str, Set[str]] = {}  # file path -> set of tags
        self._load_tags()
    
    def _load_tags(self):
        """Load tags from the database file."""
        try:
            if os.path.exists(self.tags_file):
                with open(self.tags_file, 'r') as f:
                    data = json.load(f)
                    self.tags = {tag: set(paths) for tag, paths in data.get('tags', {}).items()}
                    self.file_tags = {path: set(tags) for path, tags in data.get('file_tags', {}).items()}
        except Exception:
            # Initialize with empty data if loading fails
            self.tags = {}
            self.file_tags = {}
    
    def _save_tags(self):
        """Save tags to the database file."""
        try:
            data = {
                'tags': {tag: list(paths) for tag, paths in self.tags.items()},
                'file_tags': {path: list(tags) for path, tags in self.file_tags.items()},
                'last_modified': datetime.now().isoformat()
            }
            
            with open(self.tags_file, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception:
            return False
    
    def add_tag(self, file_path: str, tag: str) -> bool:
        """
        Add a tag to a file.
        
        Args:
            file_path: Path to the file
            tag: Tag to add
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(file_path):
            return False
        
        # Initialize sets if they don't exist
        if tag not in self.tags:
            self.tags[tag] = set()
        if file_path not in self.file_tags:
            self.file_tags[file_path] = set()
        
        # Add the tag
        self.tags[tag].add(file_path)
        self.file_tags[file_path].add(tag)
        
        return self._save_tags()
    
    def remove_tag(self, file_path: str, tag: str) -> bool:
        """
        Remove a tag from a file.
        
        Args:
            file_path: Path to the file
            tag: Tag to remove
            
        Returns:
            True if successful, False otherwise
        """
        if tag in self.tags and file_path in self.tags[tag]:
            self.tags[tag].remove(file_path)
            if not self.tags[tag]:
                del self.tags[tag]
        
        if file_path in self.file_tags and tag in self.file_tags[file_path]:
            self.file_tags[file_path].remove(tag)
            if not self.file_tags[file_path]:
                del self.file_tags[file_path]
        
        return self._save_tags()
    
    def get_file_tags(self, file_path: str) -> Set[str]:
        """
        Get all tags for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Set of tags
        """
        return self.file_tags.get(file_path, set())
    
    def get_tagged_files(self, tag: str) -> Set[str]:
        """
        Get all files with a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            Set of file paths
        """
        return self.tags.get(tag, set())
    
    def get_all_tags(self) -> List[str]:
        """
        Get all available tags.
        
        Returns:
            List of tags
        """
        return sorted(self.tags.keys())
    
    def search_by_tags(self, tags: List[str], match_all: bool = False) -> Set[str]:
        """
        Search for files that have specific tags.
        
        Args:
            tags: List of tags to search for
            match_all: If True, files must have all tags; if False, files can have any of the tags
            
        Returns:
            Set of matching file paths
        """
        if not tags:
            return set()
        
        if match_all:
            # Files must have all specified tags
            result = self.get_tagged_files(tags[0])
            for tag in tags[1:]:
                result &= self.get_tagged_files(tag)
        else:
            # Files can have any of the specified tags
            result = set()
            for tag in tags:
                result |= self.get_tagged_files(tag)
        
        return result
    
    def remove_file_tags(self, file_path: str) -> bool:
        """
        Remove all tags from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful, False otherwise
        """
        if file_path in self.file_tags:
            # Remove file from all tag sets
            for tag in self.file_tags[file_path]:
                if tag in self.tags:
                    self.tags[tag].remove(file_path)
                    if not self.tags[tag]:
                        del self.tags[tag]
            
            # Remove file's tag set
            del self.file_tags[file_path]
            return self._save_tags()
        
        return True
    
    def rename_tag(self, old_tag: str, new_tag: str) -> bool:
        """
        Rename a tag across all files.
        
        Args:
            old_tag: Current tag name
            new_tag: New tag name
            
        Returns:
            True if successful, False otherwise
        """
        if old_tag not in self.tags or new_tag in self.tags:
            return False
        
        # Move all files from old tag to new tag
        self.tags[new_tag] = self.tags[old_tag]
        del self.tags[old_tag]
        
        # Update file tags
        for file_path in self.tags[new_tag]:
            if file_path in self.file_tags:
                self.file_tags[file_path].remove(old_tag)
                self.file_tags[file_path].add(new_tag)
        
        return self._save_tags()
    
    def get_tag_stats(self) -> Dict[str, int]:
        """
        Get statistics about tag usage.
        
        Returns:
            Dictionary mapping tags to their usage count
        """
        return {tag: len(paths) for tag, paths in self.tags.items()} 