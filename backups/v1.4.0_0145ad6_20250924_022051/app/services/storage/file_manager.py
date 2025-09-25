"""
File Manager for Storage Operations

Handles file operations, cleanup, and storage management.
"""

import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

from ...utils.logging.setup import get_logger

logger = get_logger(__name__)


class FileManagerError(Exception):
    """Exception raised when file management operations fail"""
    pass


class FileManager:
    """
    File manager for storage operations and cleanup.
    
    Handles:
    - File cleanup based on age
    - Storage space monitoring
    - File metadata operations
    - Safe file operations
    """
    
    def __init__(self, base_directory: Path):
        """
        Initialize file manager
        
        Args:
            base_directory: Base directory for file operations
        """
        self.base_directory = Path(base_directory)
        self.base_directory.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"File manager initialized for: {self.base_directory}")
    
    def cleanup_old_files(self, max_age_days: int = 30, file_patterns: List[str] = None) -> int:
        """
        Clean up old files based on age
        
        Args:
            max_age_days: Maximum age of files to keep (in days)
            file_patterns: List of file patterns to match (default: ['*.xlsx', '*.docx', '*.pdf'])
            
        Returns:
            Number of files cleaned up
        """
        if file_patterns is None:
            file_patterns = ['*.xlsx', '*.docx', '*.pdf']
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        cleanup_count = 0
        
        logger.info(f"Starting cleanup of files older than {max_age_days} days")
        
        try:
            for pattern in file_patterns:
                for file_path in self.base_directory.glob(pattern):
                    try:
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        if file_mtime < cutoff_date:
                            logger.debug(f"Removing old file: {file_path.name}")
                            file_path.unlink()
                            cleanup_count += 1
                            
                    except Exception as e:
                        logger.warning(f"Failed to process file {file_path}: {e}")
            
            logger.info(f"Cleanup completed - Removed {cleanup_count} files")
            return cleanup_count
            
        except Exception as e:
            raise FileManagerError(f"Cleanup operation failed: {e}")
    
    def get_directory_size(self) -> Dict[str, Any]:
        """
        Get directory size information
        
        Returns:
            Dictionary with size information
        """
        try:
            total_size = 0
            file_count = 0
            
            for file_path in self.base_directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count,
                'directory': str(self.base_directory)
            }
            
        except Exception as e:
            raise FileManagerError(f"Failed to calculate directory size: {e}")
    
    def list_files_by_type(self, file_extension: str = None) -> List[Dict[str, Any]]:
        """
        List files by type with metadata
        
        Args:
            file_extension: File extension to filter by (e.g., '.xlsx')
            
        Returns:
            List of file metadata dictionaries
        """
        files = []
        
        try:
            pattern = f"*{file_extension}" if file_extension else "*"
            
            for file_path in self.base_directory.glob(pattern):
                if file_path.is_file():
                    stat = file_path.stat()
                    
                    files.append({
                        'name': file_path.name,
                        'path': str(file_path),
                        'size_bytes': stat.st_size,
                        'size_mb': round(stat.st_size / (1024 * 1024), 3),
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'extension': file_path.suffix.lower()
                    })
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
            return files
            
        except Exception as e:
            raise FileManagerError(f"Failed to list files: {e}")
    
    def safe_delete_file(self, file_path: str) -> bool:
        """
        Safely delete a file with error handling
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            path = Path(file_path)
            
            # Security check - ensure file is within base directory
            if not self._is_path_safe(path):
                raise FileManagerError(f"Unsafe file path: {file_path}")
            
            if path.exists() and path.is_file():
                path.unlink()
                logger.info(f"File deleted: {path.name}")
                return True
            else:
                logger.warning(f"File not found: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def safe_move_file(self, source_path: str, destination_path: str) -> bool:
        """
        Safely move a file with error handling
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            
        Returns:
            True if move was successful
        """
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            
            # Security checks
            if not self._is_path_safe(source) or not self._is_path_safe(destination):
                raise FileManagerError("Unsafe file paths")
            
            if not source.exists():
                raise FileManagerError(f"Source file not found: {source_path}")
            
            # Create destination directory if needed
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(str(source), str(destination))
            logger.info(f"File moved: {source.name} -> {destination}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to move file {source_path} -> {destination_path}: {e}")
            return False
    
    def get_file_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific file
        
        Args:
            file_path: Path to the file
            
        Returns:
            File metadata dictionary or None if file not found
        """
        try:
            path = Path(file_path)
            
            if not path.exists() or not path.is_file():
                return None
            
            stat = path.stat()
            
            return {
                'name': path.name,
                'path': str(path.resolve()),
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 3),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'extension': path.suffix.lower(),
                'parent_directory': str(path.parent),
                'is_readable': path.is_file() and path.stat().st_mode & 0o444,
                'is_writable': path.is_file() and path.stat().st_mode & 0o222
            }
            
        except Exception as e:
            logger.error(f"Failed to get metadata for {file_path}: {e}")
            return None
    
    def archive_old_files(self, archive_directory: str, max_age_days: int = 90) -> int:
        """
        Archive old files to a different directory instead of deleting
        
        Args:
            archive_directory: Directory to move old files to
            max_age_days: Age threshold for archiving
            
        Returns:
            Number of files archived
        """
        archive_path = Path(archive_directory)
        archive_path.mkdir(parents=True, exist_ok=True)
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        archive_count = 0
        
        logger.info(f"Starting archival of files older than {max_age_days} days")
        
        try:
            for file_path in self.base_directory.glob('*'):
                if file_path.is_file():
                    try:
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        if file_mtime < cutoff_date:
                            destination = archive_path / file_path.name
                            
                            # Handle name conflicts
                            counter = 1
                            while destination.exists():
                                stem = file_path.stem
                                suffix = file_path.suffix
                                destination = archive_path / f"{stem}_{counter}{suffix}"
                                counter += 1
                            
                            shutil.move(str(file_path), str(destination))
                            logger.debug(f"Archived file: {file_path.name} -> {destination.name}")
                            archive_count += 1
                            
                    except Exception as e:
                        logger.warning(f"Failed to archive file {file_path}: {e}")
            
            logger.info(f"Archive completed - Moved {archive_count} files")
            return archive_count
            
        except Exception as e:
            raise FileManagerError(f"Archive operation failed: {e}")
    
    def _is_path_safe(self, path: Path) -> bool:
        """
        Check if a path is safe (within base directory)
        
        Args:
            path: Path to check
            
        Returns:
            True if path is safe
        """
        try:
            # Resolve both paths to absolute paths
            abs_path = path.resolve()
            abs_base = self.base_directory.resolve()
            
            # Check if the path is within the base directory
            return str(abs_path).startswith(str(abs_base))
            
        except Exception:
            return False


def create_file_manager(base_directory: str) -> FileManager:
    """
    Factory function to create a file manager
    
    Args:
        base_directory: Base directory for file operations
        
    Returns:
        Configured FileManager instance
    """
    return FileManager(Path(base_directory))


__all__ = ['FileManager', 'FileManagerError', 'create_file_manager']