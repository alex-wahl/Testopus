#!/usr/bin/env python3
"""File utility functions for Allure report customization.

This module provides common file operations used in the Allure report customization process.
"""

import os
import glob
import logging
import shutil
from typing import Optional, List, Dict, Any, Union, Tuple

# Set up logging
logger = logging.getLogger('allure-customizer.file-utils')

def ensure_dir_exists(directory_path: str) -> bool:
    """Ensure directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to directory to ensure exists
        
    Returns:
        bool: True if directory exists or was created, False on error
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory_path}: {str(e)}")
        return False

def read_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """Read file contents safely.
    
    Args:
        file_path: Path to file to read
        encoding: Character encoding to use (default: utf-8)
        
    Returns:
        Optional[str]: File contents or None if file could not be read
    """
    if not os.path.exists(file_path):
        logger.warning(f"File does not exist: {file_path}")
        return None
        
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading {file_path}: {str(e)}")
        return None

def write_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """Write content to file safely.
    
    Args:
        file_path: Path to file to write
        content: Content to write to file
        encoding: Character encoding to use (default: utf-8)
        
    Returns:
        bool: True if file was written successfully, False otherwise
    """
    try:
        # Ensure directory exists
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            ensure_dir_exists(dir_path)
            
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Error writing to {file_path}: {str(e)}")
        return False

def modify_file(file_path: str, modify_func, encoding: str = 'utf-8') -> bool:
    """Read file, modify content, and write back.
    
    Args:
        file_path: Path to file to modify
        modify_func: Function that takes content string and returns modified content
        encoding: Character encoding to use (default: utf-8)
        
    Returns:
        bool: True if file was modified successfully, False otherwise
    """
    content = read_file(file_path, encoding)
    if content is None:
        return False
        
    try:
        modified_content = modify_func(content)
        return write_file(file_path, modified_content, encoding)
    except Exception as e:
        logger.error(f"Error modifying content for {file_path}: {str(e)}")
        return False

def find_files(base_dir: str, pattern: str, recursive: bool = True) -> List[str]:
    """Find files matching pattern.
    
    Args:
        base_dir: Base directory to search
        pattern: Glob pattern to match
        recursive: Whether to search recursively (default: True)
        
    Returns:
        List[str]: List of matching file paths
    """
    try:
        if not os.path.exists(base_dir):
            logger.warning(f"Base directory does not exist: {base_dir}")
            return []
            
        if recursive:
            return glob.glob(os.path.join(base_dir, "**", pattern), recursive=True)
        else:
            return glob.glob(os.path.join(base_dir, pattern), recursive=False)
    except Exception as e:
        logger.error(f"Error finding files in {base_dir} with pattern {pattern}: {str(e)}")
        return []

def copy_directory(src_dir: str, dst_dir: str) -> bool:
    """Copy directory contents safely.
    
    Args:
        src_dir: Source directory
        dst_dir: Destination directory
        
    Returns:
        bool: True if directory was copied successfully, False otherwise
    """
    if not os.path.exists(src_dir):
        logger.warning(f"Source directory does not exist: {src_dir}")
        return False
        
    try:
        ensure_dir_exists(dst_dir)
        
        # If destination exists, remove it first (shutil.copytree requirement)
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)
            
        shutil.copytree(src_dir, dst_dir)
        return True
    except Exception as e:
        logger.error(f"Error copying directory from {src_dir} to {dst_dir}: {str(e)}")
        return False

def copy_files(src_dir: str, dst_dir: str, file_pattern: str = "*") -> Tuple[int, int]:
    """Copy files matching pattern from source to destination.
    
    Args:
        src_dir: Source directory
        dst_dir: Destination directory
        file_pattern: Pattern of files to copy (default: "*")
        
    Returns:
        Tuple[int, int]: Count of successfully copied files and total files
    """
    if not os.path.exists(src_dir):
        logger.warning(f"Source directory does not exist: {src_dir}")
        return 0, 0
        
    try:
        ensure_dir_exists(dst_dir)
        
        # Find all files to copy
        files = glob.glob(os.path.join(src_dir, file_pattern))
        
        # Copy each file individually
        success_count = 0
        for src_file in files:
            if os.path.isfile(src_file):
                dst_file = os.path.join(dst_dir, os.path.basename(src_file))
                try:
                    shutil.copy2(src_file, dst_file)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error copying {src_file} to {dst_file}: {str(e)}")
        
        return success_count, len(files)
    except Exception as e:
        logger.error(f"Error copying files from {src_dir} to {dst_dir}: {str(e)}")
        return 0, 0 