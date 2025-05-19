"""
File operations module for the File System Explorer.
"""

import os
import shutil
from typing import List, Tuple, Optional
from datetime import datetime

class FileOperations:
    """Class handling file system operations."""
    
    @staticmethod
    def copy_files(source_paths: List[str], destination: str) -> Tuple[int, List[str]]:
        """
        Copy multiple files to a destination directory.
        
        Args:
            source_paths: List of source file paths
            destination: Destination directory path
            
        Returns:
            Tuple of (success_count, failed_paths)
        """
        success_count = 0
        failed_paths = []
        
        for source in source_paths:
            try:
                if os.path.isfile(source):
                    shutil.copy2(source, destination)
                elif os.path.isdir(source):
                    shutil.copytree(source, os.path.join(destination, os.path.basename(source)))
                success_count += 1
            except Exception:
                failed_paths.append(source)
        
        return success_count, failed_paths
    
    @staticmethod
    def move_files(source_paths: List[str], destination: str) -> Tuple[int, List[str]]:
        """
        Move multiple files to a destination directory.
        
        Args:
            source_paths: List of source file paths
            destination: Destination directory path
            
        Returns:
            Tuple of (success_count, failed_paths)
        """
        success_count = 0
        failed_paths = []
        
        for source in source_paths:
            try:
                shutil.move(source, destination)
                success_count += 1
            except Exception:
                failed_paths.append(source)
        
        return success_count, failed_paths
    
    @staticmethod
    def delete_files(paths: List[str], recursive: bool = False) -> Tuple[int, List[str]]:
        """
        Delete multiple files or directories.
        
        Args:
            paths: List of file/directory paths to delete
            recursive: Whether to delete directories recursively
            
        Returns:
            Tuple of (success_count, failed_paths)
        """
        success_count = 0
        failed_paths = []
        
        for path in paths:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    success_count += 1
                elif os.path.isdir(path):
                    if recursive:
                        shutil.rmtree(path)
                        success_count += 1
                    else:
                        os.rmdir(path)
                        success_count += 1
            except Exception:
                failed_paths.append(path)
        
        return success_count, failed_paths
    
    @staticmethod
    def rename_file(old_path: str, new_path: str) -> Tuple[bool, str]:
        """
        Rename a file or directory.
        
        Args:
            old_path: Current file/directory path
            new_path: New path for the file/directory
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            print(f"Attempting to rename: {old_path} -> {new_path}")  # Debug log
            
            # Ensure the parent directory exists
            parent_dir = os.path.dirname(new_path)
            if not os.path.exists(parent_dir):
                print(f"Parent directory does not exist: {parent_dir}")  # Debug log
                return False, f"Parent directory does not exist: {parent_dir}"
            
            # Check if the new path already exists
            if os.path.exists(new_path):
                print(f"Target path already exists: {new_path}")  # Debug log
                return False, f"File or directory already exists: {new_path}"
            
            # Check if we have write permission to the parent directory
            if not os.access(parent_dir, os.W_OK):
                print(f"No write permission for parent directory: {parent_dir}")  # Debug log
                return False, f"No permission to write to directory: {parent_dir}"
            
            # Check if we have write permission to the file/directory
            if not os.access(old_path, os.W_OK):
                print(f"No write permission for source: {old_path}")  # Debug log
                return False, f"No permission to modify: {old_path}"
            
            # Check if source exists
            if not os.path.exists(old_path):
                print(f"Source path does not exist: {old_path}")  # Debug log
                return False, f"Source file or directory does not exist: {old_path}"
            
            # Perform the rename
            print(f"Executing rename operation...")  # Debug log
            os.rename(old_path, new_path)
            print(f"Rename successful!")  # Debug log
            return True, ""
            
        except PermissionError as e:
            print(f"Permission error during rename: {str(e)}")  # Debug log
            return False, f"Permission denied: {str(e)}"
        except OSError as e:
            print(f"OS error during rename: {str(e)}")  # Debug log
            return False, f"Operation failed: {str(e)}"
        except Exception as e:
            print(f"Unexpected error during rename: {str(e)}")  # Debug log
            return False, f"Unexpected error: {str(e)}"
    
    @staticmethod
    def get_file_info(path: str) -> dict:
        """
        Get detailed information about a file or directory.
        
        Args:
            path: Path to the file or directory
            
        Returns:
            Dictionary containing file information
        """
        try:
            stat = os.stat(path)
            return {
                'name': os.path.basename(path),
                'path': path,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'accessed': datetime.fromtimestamp(stat.st_atime),
                'is_dir': os.path.isdir(path),
                'is_file': os.path.isfile(path),
                'is_link': os.path.islink(path),
                'extension': os.path.splitext(path)[1] if os.path.isfile(path) else None
            }
        except Exception:
            return {}
    
    @staticmethod
    def create_directory(path: str) -> bool:
        """
        Create a new directory.
        
        Args:
            path: Path where the directory should be created
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def search_files(directory: str, pattern: str, case_sensitive: bool = False) -> List[str]:
        """
        Search for files matching a pattern in a directory.
        
        Args:
            directory: Directory to search in
            pattern: Pattern to match against file names
            case_sensitive: Whether the search should be case sensitive
            
        Returns:
            List of matching file paths
        """
        matches = []
        
        if not case_sensitive:
            pattern = pattern.lower()
        
        for root, _, files in os.walk(directory):
            for file in files:
                if not case_sensitive:
                    if pattern in file.lower():
                        matches.append(os.path.join(root, file))
                else:
                    if pattern in file:
                        matches.append(os.path.join(root, file))
        
        return matches
    
    @staticmethod
    def get_directory_size(path: str) -> int:
        """
        Calculate the total size of a directory.
        
        Args:
            path: Path to the directory
            
        Returns:
            Total size in bytes
        """
        total_size = 0
        try:
            for dirpath, _, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        except Exception:
            pass
        return total_size 