import os
import json
import hashlib
import shutil
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import zipfile
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.syntax import Syntax
from rich import box
from rich.text import Text

class SimpleVCS:
    """Simple Version Control System core functionality"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.svcs_dir = self.repo_path / ".svcs"
        self.objects_dir = self.svcs_dir / "objects"
        self.commits_file = self.svcs_dir / "commits.json"
        self.staging_file = self.svcs_dir / "staging.json"
        self.head_file = self.svcs_dir / "HEAD"
        # Force UTF-8 output and disable emoji on Windows
        self.is_windows = sys.platform == "win32"
        self.console = Console(force_terminal=True, legacy_windows=False)
        
    def init_repo(self) -> bool:
        """Initialize a new repository"""
        if self.svcs_dir.exists():
            self.console.print(f"[yellow]WARNING: Repository already exists at[/yellow] [cyan]{self.repo_path}[/cyan]")
            return False

        self.console.print("[cyan]Initializing repository...[/cyan]")

        # Create directory structure
        self.svcs_dir.mkdir()
        self.objects_dir.mkdir()

        # Initialize files
        self._write_json(self.commits_file, [])
        self._write_json(self.staging_file, {})
        self.head_file.write_text("0")  # Start with commit 0

        panel = Panel(
            f"[green]SUCCESS[/green] Repository initialized at [cyan]{self.repo_path}[/cyan]\n\n"
            "[dim]Structure created:[/dim]\n"
            "  - .svcs/objects/ - File storage\n"
            "  - .svcs/commits.json - Commit history\n"
            "  - .svcs/staging.json - Staged files\n"
            "  - .svcs/HEAD - Current commit",
            title="[bold green]SimpleVCS Repository[/bold green]",
            border_style="green",
            box=box.ROUNDED
        )
        self.console.print(panel)
        return True
    
    def add_file(self, file_path: str) -> bool:
        """Add a file to staging area"""
        if not self._check_repo():
            return False

        file_path = Path(file_path).resolve()  # Convert to absolute path
        if not file_path.exists():
            self.console.print(f"[red]ERROR: File not found:[/red] [yellow]{file_path}[/yellow]")
            return False

        if not file_path.is_file():
            self.console.print(f"[red]ERROR: Not a file:[/red] [yellow]{file_path}[/yellow]")
            return False

        # Check if file is within repository
        try:
            relative_path = file_path.relative_to(self.repo_path)
        except ValueError:
            self.console.print(f"[red]ERROR: File not in repository:[/red] [yellow]{file_path}[/yellow]")
            return False

        # Calculate file hash and store
        file_hash = self._calculate_file_hash(file_path)
        self._store_object(file_hash, file_path.read_bytes())

        # Add to staging
        staging = self._read_json(self.staging_file)
        staging[str(relative_path)] = {
            "hash": file_hash,
            "size": file_path.stat().st_size,
            "modified": file_path.stat().st_mtime
        }
        self._write_json(self.staging_file, staging)

        # Format file size
        size_kb = file_path.stat().st_size / 1024
        size_str = f"{size_kb:.1f}KB" if size_kb < 1024 else f"{size_kb/1024:.1f}MB"

        self.console.print(f"[green]Added:[/green] [cyan]{relative_path}[/cyan] [dim]({size_str})[/dim]")
        return True
    
    def commit(self, message: Optional[str] = None) -> bool:
        """Commit staged changes"""
        if not self._check_repo():
            return False

        staging = self._read_json(self.staging_file)
        if not staging:
            self.console.print("[yellow]WARNING: No changes staged for commit[/yellow]")
            self.console.print("[dim]Tip: Use 'svcs add <file>' to stage files[/dim]")
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

        # Create summary panel
        files_list = "\n".join([f"  - [cyan]{f}[/cyan]" for f in list(staging.keys())[:5]])
        if len(staging) > 5:
            files_list += f"\n  [dim]... and {len(staging) - 5} more file(s)[/dim]"

        panel = Panel(
            f"[bold green]Commit #{commit['id']}[/bold green]\n\n"
            f"[bold]Message:[/bold] {commit['message']}\n"
            f"[bold]Files:[/bold] {len(staging)} file(s)\n\n"
            f"{files_list}",
            title="[bold green]Commit Successful[/bold green]",
            border_style="green",
            box=box.ROUNDED
        )
        self.console.print(panel)
        return True
    
    def show_diff(self, commit_id1: Optional[int] = None, commit_id2: Optional[int] = None) -> bool:
        """Show differences between commits"""
        if not self._check_repo():
            return False

        commits = self._read_json(self.commits_file)
        if not commits:
            self.console.print("[yellow]WARNING: No commits found[/yellow]")
            return False

        # Default to comparing last two commits
        if commit_id1 is None and commit_id2 is None:
            if len(commits) < 2:
                self.console.print("[yellow]WARNING: Need at least 2 commits to show diff[/yellow]")
                return False
            commit1 = commits[-2]
            commit2 = commits[-1]
        else:
            commit1 = self._get_commit_by_id(commit_id1 or (len(commits) - 1))
            commit2 = self._get_commit_by_id(commit_id2 or len(commits))

        if not commit1 or not commit2:
            self.console.print("[red]ERROR: Invalid commit IDs[/red]")
            return False

        # Create comparison table
        table = Table(
            title=f"[bold]Differences: Commit #{commit1['id']} to Commit #{commit2['id']}[/bold]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("Status", style="bold", width=10)
        table.add_column("File", style="cyan")
        table.add_column("Details", style="dim")

        files1 = set(commit1["files"].keys())
        files2 = set(commit2["files"].keys())

        has_changes = False

        # New files
        new_files = sorted(files2 - files1)
        for file in new_files:
            size = commit2["files"][file]["size"]
            size_str = f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/(1024*1024):.1f}MB"
            table.add_row("[green]+ Added[/green]", file, f"Size: {size_str}")
            has_changes = True

        # Deleted files
        deleted_files = sorted(files1 - files2)
        for file in deleted_files:
            table.add_row("[red]- Deleted[/red]", file, "")
            has_changes = True

        # Modified files
        common_files = files1 & files2
        modified_files = []
        for file in sorted(common_files):
            if commit1["files"][file]["hash"] != commit2["files"][file]["hash"]:
                size1 = commit1["files"][file]["size"]
                size2 = commit2["files"][file]["size"]
                diff = size2 - size1
                diff_str = f"+{diff/1024:.1f}KB" if diff > 0 else f"{diff/1024:.1f}KB"
                table.add_row("[yellow]M Modified[/yellow]", file, f"Size change: {diff_str}")
                modified_files.append(file)
                has_changes = True

        if not has_changes:
            self.console.print("[dim]No differences found between commits[/dim]")
        else:
            self.console.print(table)
            self.console.print(f"\n[dim]Summary: [green]{len(new_files)} added[/green], "
                             f"[yellow]{len(modified_files)} modified[/yellow], "
                             f"[red]{len(deleted_files)} deleted[/red][/dim]")

        return True
    
    def show_log(self, limit: Optional[int] = None) -> bool:
        """Show commit history"""
        if not self._check_repo():
            return False

        commits = self._read_json(self.commits_file)
        if not commits:
            self.console.print("[yellow]WARNING: No commits found[/yellow]")
            self.console.print("[dim]Tip: Use 'svcs commit -m \"message\"' to create your first commit[/dim]")
            return False

        commits_to_show = commits[-limit:] if limit else commits
        commits_to_show.reverse()  # Show newest first

        # Create commits table
        table = Table(
            title="[bold cyan]Commit History[/bold cyan]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("ID", justify="center", style="cyan", width=6)
        table.add_column("Date", style="green", width=19)
        table.add_column("Message", style="white")
        table.add_column("Files", justify="center", style="yellow", width=7)
        table.add_column("Parent", justify="center", style="dim", width=7)

        current_commit_id = self._get_current_commit_id()

        for commit in commits_to_show:
            commit_id = str(commit['id'])
            if commit['id'] == current_commit_id:
                commit_id = f"* {commit_id}"  # Mark current commit

            date_str = datetime.fromtimestamp(commit['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            message = commit['message']
            if len(message) > 50:
                message = message[:47] + "..."
            files_count = str(len(commit['files']))
            parent = str(commit.get('parent', '-'))

            # Style current commit differently
            if commit['id'] == current_commit_id:
                table.add_row(
                    f"[bold cyan]{commit_id}[/bold cyan]",
                    date_str,
                    f"[bold]{message}[/bold]",
                    files_count,
                    parent
                )
            else:
                table.add_row(commit_id, date_str, message, files_count, parent)

        self.console.print(table)

        if limit and len(commits) > limit:
            self.console.print(f"\n[dim]Showing last {limit} of {len(commits)} commits[/dim]")

        return True
    
    def status(self) -> bool:
        """Show repository status"""
        if not self._check_repo():
            return False

        staging = self._read_json(self.staging_file)
        current_commit = self._get_current_commit()
        total_commits = len(self._read_json(self.commits_file))

        # Create status panel
        status_text = f"[bold]Repository:[/bold] [cyan]{self.repo_path.name}[/cyan]\n"
        status_text += f"[bold]Location:[/bold] [dim]{self.repo_path}[/dim]\n"
        status_text += f"[bold]Current Commit:[/bold] [green]#{current_commit['id']}[/green] " if current_commit else "[bold]Current Commit:[/bold] [yellow]None (no commits yet)[/yellow]\n"
        if current_commit:
            status_text += f"[dim]({current_commit['message']})[/dim]\n"
        status_text += f"[bold]Total Commits:[/bold] {total_commits}"

        panel = Panel(
            status_text,
            title="[bold cyan]Repository Status[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED
        )
        self.console.print(panel)

        # Show staged files
        if staging:
            table = Table(
                title="[bold yellow]Staged Files[/bold yellow]",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold yellow"
            )
            table.add_column("File", style="cyan")
            table.add_column("Size", justify="right", style="green")
            table.add_column("Hash", style="dim", width=16)

            for file, info in staging.items():
                size = info['size']
                size_str = f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/(1024*1024):.1f}MB"
                hash_short = info['hash'][:14] + "..."
                table.add_row(file, size_str, hash_short)

            self.console.print("\n", table)
            self.console.print(f"[dim]Ready to commit {len(staging)} file(s)[/dim]")
        else:
            self.console.print("\n[yellow]No files staged[/yellow]")
            self.console.print("[dim]Use 'svcs add <file>' to stage files for commit[/dim]")

        return True
    
    # Helper methods
    def _check_repo(self) -> bool:
        """Check if repository is initialized"""
        if not self.svcs_dir.exists():
            self.console.print("[red]ERROR: Not a SimpleVCS repository[/red]")
            self.console.print("[dim]Tip: Run 'svcs init' to initialize a repository[/dim]")
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

    def quick_revert(self, commit_id: int) -> bool:
        """Quickly revert to a specific commit"""
        if not self._check_repo():
            return False

        commit = self._get_commit_by_id(commit_id)
        if not commit:
            self.console.print(f"[red]ERROR: Commit #{commit_id} not found[/red]")
            return False

        self.console.print(f"[cyan]Reverting to commit #{commit_id}...[/cyan]")

        # Restore files from the specified commit
        for file_path, file_info in commit["files"].items():
            target_path = self.repo_path / file_path
            obj_path = self.objects_dir / file_info["hash"]

            # Create parent directories if they don't exist
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file from objects to target location
            if obj_path.exists():
                shutil.copy2(obj_path, target_path)

        # Update HEAD to point to the reverted commit
        self.head_file.write_text(str(commit_id))

        panel = Panel(
            f"[bold green]Successfully reverted to commit #{commit_id}[/bold green]\n\n"
            f"[bold]Message:[/bold] {commit['message']}\n"
            f"[bold]Files restored:[/bold] {len(commit['files'])}\n"
            f"[bold]Date:[/bold] {datetime.fromtimestamp(commit['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}",
            title="[bold green]Revert Complete[/bold green]",
            border_style="green",
            box=box.ROUNDED
        )
        self.console.print(panel)
        return True

    def create_snapshot(self, name: str = None) -> bool:
        """Create a compressed snapshot of the current repository state"""
        if not self._check_repo():
            return False

        snapshot_name = name or f"snapshot_{int(time.time())}"
        snapshot_path = self.repo_path / f"{snapshot_name}.zip"

        self.console.print("[cyan]Creating snapshot...[/cyan]")

        # Count files first
        file_count = 0
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d != '.svcs']
            file_count += len(files)

        # Create a zip archive of all tracked files
        with zipfile.ZipFile(snapshot_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.repo_path):
                # Skip .svcs directory
                dirs[:] = [d for d in dirs if d != '.svcs']

                for file in files:
                    file_path = Path(root) / file
                    if file_path != snapshot_path:  # Don't include the snapshot itself
                        arc_path = file_path.relative_to(self.repo_path)
                        zipf.write(file_path, arc_path)

        snapshot_size = snapshot_path.stat().st_size
        size_str = f"{snapshot_size/1024:.1f}KB" if snapshot_size < 1024*1024 else f"{snapshot_size/(1024*1024):.1f}MB"

        panel = Panel(
            f"[bold green]Snapshot created successfully[/bold green]\n\n"
            f"[bold]Name:[/bold] [cyan]{snapshot_name}.zip[/cyan]\n"
            f"[bold]Location:[/bold] [dim]{snapshot_path}[/dim]\n"
            f"[bold]Size:[/bold] {size_str}\n"
            f"[bold]Files:[/bold] {file_count}",
            title="[bold green]Snapshot Created[/bold green]",
            border_style="green",
            box=box.ROUNDED
        )
        self.console.print(panel)
        return True

    def restore_from_snapshot(self, snapshot_path: str) -> bool:
        """Restore repository from a snapshot"""
        snapshot_path = Path(snapshot_path)
        if not snapshot_path.exists():
            self.console.print(f"[red]ERROR: Snapshot not found:[/red] [yellow]{snapshot_path}[/yellow]")
            return False

        self.console.print("[cyan]Restoring from snapshot...[/cyan]")

        # Extract the zip archive
        with zipfile.ZipFile(snapshot_path, 'r') as zipf:
            file_list = zipf.namelist()

            # Clear current files (but preserve .svcs directory)
            for item in self.repo_path.iterdir():
                if item.name != '.svcs':
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()

            # Extract all files
            zipf.extractall(self.repo_path)

        panel = Panel(
            f"[bold green]Repository restored successfully[/bold green]\n\n"
            f"[bold]Snapshot:[/bold] [cyan]{snapshot_path.name}[/cyan]\n"
            f"[bold]Files restored:[/bold] {len(file_list)}",
            title="[bold green]Restore Complete[/bold green]",
            border_style="green",
            box=box.ROUNDED
        )
        self.console.print(panel)
        return True

    def compress_objects(self) -> bool:
        """Compress stored objects to save space"""
        if not self._check_repo():
            return False

        original_size = sum(f.stat().st_size for f in self.objects_dir.glob('*') if f.is_file())
        obj_files = [f for f in self.objects_dir.glob('*') if f.is_file() and f.stat().st_size > 1024]

        if not obj_files:
            self.console.print("[yellow]WARNING: No objects to compress (files are too small)[/yellow]")
            return True

        self.console.print("[cyan]Compressing objects...[/cyan]")

        # For each object file, compress it if it's large enough to benefit
        for obj_file in obj_files:
            # Create a compressed version with .gz extension
            compressed_path = obj_file.with_suffix(obj_file.suffix + '.gz')
            with open(obj_file, 'rb') as f_in:
                import gzip
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)

            # Replace original with compressed version
            obj_file.unlink()
            # Decompress back to original name for compatibility
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(obj_file, 'wb') as f_out:
                    f_out.write(f_in.read())
            compressed_path.unlink()

        new_size = sum(f.stat().st_size for f in self.objects_dir.glob('*') if f.is_file())
        saved_space = original_size - new_size
        saved_percent = (saved_space / original_size * 100) if original_size > 0 else 0

        # Format sizes
        orig_str = f"{original_size/1024:.1f}KB" if original_size < 1024*1024 else f"{original_size/(1024*1024):.1f}MB"
        new_str = f"{new_size/1024:.1f}KB" if new_size < 1024*1024 else f"{new_size/(1024*1024):.1f}MB"
        saved_str = f"{saved_space/1024:.1f}KB" if saved_space < 1024*1024 else f"{saved_space/(1024*1024):.1f}MB"

        panel = Panel(
            f"[bold green]Compression completed successfully[/bold green]\n\n"
            f"[bold]Original size:[/bold] {orig_str}\n"
            f"[bold]New size:[/bold] {new_str}\n"
            f"[bold]Space saved:[/bold] [green]{saved_str}[/green] [dim]({saved_percent:.1f}%)[/dim]\n"
            f"[bold]Objects compressed:[/bold] {len(obj_files)}",
            title="[bold green]Compression Complete[/bold green]",
            border_style="green",
            box=box.ROUNDED
        )
        self.console.print(panel)
        return True
