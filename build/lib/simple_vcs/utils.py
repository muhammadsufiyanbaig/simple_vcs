import os
from pathlib import Path
from typing import List

def get_all_files(directory: str, ignore_patterns: List[str] = None) -> List[str]:
    """Get all files in directory, excluding ignored patterns"""
    if ignore_patterns is None:
        ignore_patterns = ['.svcs', '__pycache__', '.git', '.DS_Store']
    
    files = []
    for root, dirs, filenames in os.walk(directory):
        # Remove ignored directories
        dirs[:] = [d for d in dirs if not any(pattern in d for pattern in ignore_patterns)]
        
        for filename in filenames:
            # Skip ignored files
            if any(pattern in filename for pattern in ignore_patterns):
                continue
                
            file_path = os.path.join(root, filename)
            files.append(file_path)
    
    return files

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"