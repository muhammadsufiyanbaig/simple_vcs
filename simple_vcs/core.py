import os
import json
import hashlib
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class SimpleVCS:
    """Simple Version Control System core functionality"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.svcs_dir = self.repo_path / ".svcs"
        self.objects_dir = self.svcs_dir / "objects"
        self.commits_file = self.svcs_dir / "commits.json"
        self.staging_file = self.svcs_dir / "staging.json"
        self.head_file = self.svcs_dir / "HEAD"
        
    def init_repo(self) -> bool:
        """Initialize a new repository"""
        if self.svcs_dir.exists():
            print(f"Repository already exists at {self.repo_path}")
            return False
            
        # Create directory structure
        self.svcs_dir.mkdir()
        self.objects_dir.mkdir()
        
        # Initialize files
        self._write_json(self.commits_file, [])
        self._write_json(self.staging_file, {})
        self.head_file.write_text("0")  # Start with commit 0
        
        print(f"Initialized empty SimpleVCS repository at {self.repo_path}")
        return True
    
    def add_file(self, file_path: str) -> bool:
        """Add a file to staging area"""
        if not self._check_repo():
            return False
            
        file_path = Path(file_path).resolve()  # Convert to absolute path
        if not file_path.exists():
            print(f"File {file_path} does not exist")
            return False
            
        if not file_path.is_file():
            print(f"{file_path} is not a file")
            return False
            
        # Check if file is within repository
        try:
            relative_path = file_path.relative_to(self.repo_path)
        except ValueError:
            print(f"File {file_path} is not within the repository")
            return False
            
        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)
        
        # Store file content in objects
        self._store_object(file_hash, file_path.read_bytes())
        
        # Add to staging
        staging = self._read_json(self.staging_file)
        staging[str(relative_path)] = {
            "hash": file_hash,
            "size": file_path.stat().st_size,
            "modified": file_path.stat().st_mtime
        }
        self._write_json(self.staging_file, staging)
        
        print(f"Added {file_path.name} to staging area")
        return True
    
    def commit(self, message: Optional[str] = None) -> bool:
        """Commit staged changes"""
        if not self._check_repo():
            return False
            
        staging = self._read_json(self.staging_file)
        if not staging:
            print("No changes to commit")
            return False
            
        # Create commit object
        commit = {
            "id": len(self._read_json(self.commits_file)) + 1,
            "message": message or f"Commit at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "timestamp": time.time(),
            "files": staging.copy(),
            "parent": self._get_current_commit_id()
        }
        
        # Save commit
        commits = self._read_json(self.commits_file)
        commits.append(commit)
        self._write_json(self.commits_file, commits)
        
        # Update HEAD
        self.head_file.write_text(str(commit["id"]))
        
        # Clear staging
        self._write_json(self.staging_file, {})
        
        print(f"Committed changes with ID: {commit['id']}")
        print(f"Message: {commit['message']}")
        return True
    
    def show_diff(self, commit_id1: Optional[int] = None, commit_id2: Optional[int] = None) -> bool:
        """Show differences between commits"""
        if not self._check_repo():
            return False
            
        commits = self._read_json(self.commits_file)
        if not commits:
            print("No commits found")
            return False
            
        # Default to comparing last two commits
        if commit_id1 is None and commit_id2 is None:
            if len(commits) < 2:
                print("Need at least 2 commits to show diff")
                return False
            commit1 = commits[-2]
            commit2 = commits[-1]
        else:
            commit1 = self._get_commit_by_id(commit_id1 or (len(commits) - 1))
            commit2 = self._get_commit_by_id(commit_id2 or len(commits))
            
        if not commit1 or not commit2:
            print("Invalid commit IDs")
            return False
            
        print(f"\nDifferences between commit {commit1['id']} and {commit2['id']}:")
        print("-" * 50)
        
        files1 = set(commit1["files"].keys())
        files2 = set(commit2["files"].keys())
        
        # New files
        new_files = files2 - files1
        if new_files:
            print("New files:")
            for file in new_files:
                print(f"  + {file}")
        
        # Deleted files
        deleted_files = files1 - files2
        if deleted_files:
            print("Deleted files:")
            for file in deleted_files:
                print(f"  - {file}")
        
        # Modified files
        common_files = files1 & files2
        modified_files = []
        for file in common_files:
            if commit1["files"][file]["hash"] != commit2["files"][file]["hash"]:
                modified_files.append(file)
        
        if modified_files:
            print("Modified files:")
            for file in modified_files:
                print(f"  M {file}")
        
        if not new_files and not deleted_files and not modified_files:
            print("No differences found")
            
        return True
    
    def show_log(self, limit: Optional[int] = None) -> bool:
        """Show commit history"""
        if not self._check_repo():
            return False
            
        commits = self._read_json(self.commits_file)
        if not commits:
            print("No commits found")
            return False
            
        commits_to_show = commits[-limit:] if limit else commits
        commits_to_show.reverse()  # Show newest first
        
        print("\nCommit History:")
        print("=" * 50)
        
        for commit in commits_to_show:
            print(f"Commit ID: {commit['id']}")
            print(f"Date: {datetime.fromtimestamp(commit['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Message: {commit['message']}")
            print(f"Files: {len(commit['files'])} file(s)")
            if commit.get('parent'):
                print(f"Parent: {commit['parent']}")
            print("-" * 30)
            
        return True
    
    def status(self) -> bool:
        """Show repository status"""
        if not self._check_repo():
            return False
            
        staging = self._read_json(self.staging_file)
        current_commit = self._get_current_commit()
        
        print(f"\nRepository: {self.repo_path}")
        print(f"Current commit: {current_commit['id'] if current_commit else 'None'}")
        
        if staging:
            print("\nStaged files:")
            for file, info in staging.items():
                print(f"  {file}")
        else:
            print("\nNo files staged")
            
        return True
    
    # Helper methods
    def _check_repo(self) -> bool:
        """Check if repository is initialized"""
        if not self.svcs_dir.exists():
            print("Not a SimpleVCS repository. Run 'svcs init' first.")
            return False
        return True
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _store_object(self, obj_hash: str, content: bytes):
        """Store object in objects directory"""
        obj_path = self.objects_dir / obj_hash
        if not obj_path.exists():
            obj_path.write_bytes(content)
    
    def _read_json(self, file_path: Path) -> Dict:
        """Read JSON file"""
        if not file_path.exists():
            return {}
        return json.loads(file_path.read_text())
    
    def _write_json(self, file_path: Path, data: Dict):
        """Write JSON file"""
        file_path.write_text(json.dumps(data, indent=2))
    
    def _get_current_commit_id(self) -> Optional[int]:
        """Get current commit ID"""
        if not self.head_file.exists():
            return None
        try:
            commit_id = int(self.head_file.read_text().strip())
            return commit_id if commit_id > 0 else None
        except:
            return None
    
    def _get_current_commit(self) -> Optional[Dict]:
        """Get current commit object"""
        commit_id = self._get_current_commit_id()
        if not commit_id:
            return None
        return self._get_commit_by_id(commit_id)
    
    def _get_commit_by_id(self, commit_id: int) -> Optional[Dict]:
        """Get commit by ID"""
        commits = self._read_json(self.commits_file)
        for commit in commits:
            if commit["id"] == commit_id:
                return commit
        return None
