"""
File compression utilities for the File System Explorer.
"""

import os
import zipfile
import tarfile
import shutil
from typing import List, Tuple

class Compression:
    """Class handling file compression and decompression."""
    
    @staticmethod
    def compress_files(file_paths: List[str], output_path: str, format: str = 'zip') -> Tuple[bool, str]:
        """
        Compress multiple files into an archive.
        
        Args:
            file_paths: List of files to compress
            output_path: Path for the output archive
            format: Archive format ('zip' or 'tar')
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if format == 'zip':
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in file_paths:
                        if os.path.isfile(file_path):
                            zipf.write(file_path, os.path.basename(file_path))
                        elif os.path.isdir(file_path):
                            for root, _, files in os.walk(file_path):
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    arcname = os.path.relpath(file_path, os.path.dirname(file_path))
                                    zipf.write(file_path, arcname)
            
            elif format == 'tar':
                with tarfile.open(output_path, 'w:gz') as tarf:
                    for file_path in file_paths:
                        if os.path.isfile(file_path):
                            tarf.add(file_path, os.path.basename(file_path))
                        elif os.path.isdir(file_path):
                            tarf.add(file_path, os.path.basename(file_path))
            
            else:
                return False, f"Unsupported format: {format}"
            
            return True, ""
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def decompress_archive(archive_path: str, extract_path: str) -> Tuple[bool, str]:
        """
        Decompress an archive file.
        
        Args:
            archive_path: Path to the archive file
            extract_path: Path to extract the contents to
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not os.path.exists(extract_path):
                os.makedirs(extract_path)
            
            if archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    zipf.extractall(extract_path)
            
            elif archive_path.endswith(('.tar.gz', '.tgz')):
                with tarfile.open(archive_path, 'r:gz') as tarf:
                    tarf.extractall(extract_path)
            
            elif archive_path.endswith('.tar'):
                with tarfile.open(archive_path, 'r') as tarf:
                    tarf.extractall(extract_path)
            
            else:
                return False, f"Unsupported archive format: {archive_path}"
            
            return True, ""
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_supported_formats() -> List[str]:
        """Get list of supported compression formats."""
        return ['zip', 'tar']
    
    @staticmethod
    def get_format_extensions() -> dict:
        """Get file extensions for each format."""
        return {
            'zip': '.zip',
            'tar': '.tar.gz'
        } 