import click
from .core import SimpleVCS
from rich.console import Console

console = Console()

@click.group()
@click.version_option(version="1.2.0", prog_name="SimpleVCS")
def main():
    """
    SimpleVCS - A beautiful and simple version control system

    A lightweight VCS with an intuitive interface for managing your project versions.
    """
    pass

@main.command()
@click.option('--path', default='.', help='Path where repository will be created')
def init(path):
    """Initialize a new SimpleVCS repository

    Creates a new .svcs directory with all necessary files for version control.

    Example: svcs init --path ./my-project
    """
    vcs = SimpleVCS(path)
    vcs.init_repo()

@main.command()
@click.argument('files', nargs=-1, required=True)
def add(files):
    """Add files to the staging area

    Stage files to be included in the next commit. You can add multiple files at once.

    Example: svcs add file1.txt file2.py
    """
    vcs = SimpleVCS()
    for file in files:
        vcs.add_file(file)

@main.command()
@click.option('-m', '--message', help='Commit message describing the changes')
def commit(message):
    """Commit staged changes to the repository

    Creates a new commit with all staged files. If no message is provided,
    an automatic timestamp-based message will be generated.

    Example: svcs commit -m "Add new feature"
    """
    vcs = SimpleVCS()
    vcs.commit(message)

@main.command()
@click.option('--c1', type=int, help='First commit ID (defaults to second-last commit)')
@click.option('--c2', type=int, help='Second commit ID (defaults to last commit)')
def diff(c1, c2):
    """Show differences between commits

    Compare files between two commits to see what changed. Without arguments,
    compares the last two commits.

    Example: svcs diff --c1 1 --c2 3
    """
    vcs = SimpleVCS()
    vcs.show_diff(c1, c2)

@main.command()
@click.option('--limit', type=int, help='Maximum number of commits to display')
def log(limit):
    """Show commit history

    Display a beautiful table of all commits with their messages, dates, and files.
    Use --limit to show only recent commits.

    Example: svcs log --limit 10
    """
    vcs = SimpleVCS()
    vcs.show_log(limit)

@main.command()
def status():
    """Show current repository status

    Display information about the repository including current commit,
    total commits, and staged files ready for commit.

    Example: svcs status
    """
    vcs = SimpleVCS()
    vcs.status()

@main.command()
@click.argument('commit_id', type=int)
def revert(commit_id):
    """Revert to a specific commit

    Quickly restore your repository to a previous commit state.
    All files will be restored to their state at that commit.

    Example: svcs revert 3
    """
    vcs = SimpleVCS()
    vcs.quick_revert(commit_id)

@main.command()
@click.option('--name', help='Custom name for the snapshot (optional)')
def snapshot(name):
    """Create a compressed snapshot

    Creates a ZIP archive of your entire repository (excluding .svcs directory).
    Perfect for backups or sharing your project.

    Example: svcs snapshot --name my-backup
    """
    vcs = SimpleVCS()
    vcs.create_snapshot(name)

@main.command()
@click.argument('snapshot_path', type=click.Path(exists=True))
def restore(snapshot_path):
    """Restore from a snapshot

    Restore your repository from a previously created snapshot ZIP file.
    Current files will be replaced with snapshot contents.

    Example: svcs restore snapshot_12345.zip
    """
    vcs = SimpleVCS()
    vcs.restore_from_snapshot(snapshot_path)

@main.command()
def compress():
    """Compress stored objects

    Optimize repository storage by compressing object files.
    Helps save disk space without losing any data.

    Example: svcs compress
    """
    vcs = SimpleVCS()
    vcs.compress_objects()

if __name__ == '__main__':
    main()