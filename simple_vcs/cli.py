import click
from .core import SimpleVCS
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.columns import Columns

console = Console()

class RichGroup(click.Group):
    """Custom Click Group that adds Rich formatting to help output"""

    def format_help(self, ctx, formatter):
        """Override help formatting with Rich output"""
        console = Console()

        # Beautiful header
        console.print()
        title = Text("SimpleVCS", style="bold cyan", justify="center")
        subtitle = Text("A Beautiful Version Control System", style="dim", justify="center")
        console.print(title)
        console.print(subtitle)
        console.print()

        # Description panel
        description = Panel(
            "[white]A lightweight, elegant version control system with a modern terminal interface.\n"
            "Track your files, manage versions, and keep your project history organized.[/white]",
            title="[bold cyan]About[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(0, 2)
        )
        console.print(description)
        console.print()

        # Commands section
        console.print("[bold white]Available Commands:[/bold white]")
        console.print()

        commands_info = [
            ("init", "Initialize a new repository", "cyan"),
            ("add", "Add files to staging area", "green"),
            ("commit", "Create a new commit", "green"),
            ("status", "Show repository status", "yellow"),
            ("log", "View commit history", "blue"),
            ("diff", "Compare commits", "magenta"),
            ("revert", "Revert to previous commit", "red"),
            ("snapshot", "Create backup snapshot", "cyan"),
            ("restore", "Restore from snapshot", "cyan"),
            ("compress", "Optimize storage", "yellow"),
        ]

        for cmd_name, cmd_desc, color in commands_info:
            console.print(f"  [{color}]{cmd_name:12}[/{color}] [dim]{cmd_desc}[/dim]")

        console.print()

        # Usage examples
        examples = Panel(
            "[bold]Quick Start:[/bold]\n"
            "[cyan]$[/cyan] svcs init                    [dim]# Create repository[/dim]\n"
            "[cyan]$[/cyan] svcs add file.txt            [dim]# Stage files[/dim]\n"
            "[cyan]$[/cyan] svcs commit -m \"message\"     [dim]# Save changes[/dim]\n"
            "[cyan]$[/cyan] svcs log                     [dim]# View history[/dim]\n\n"
            "[bold]Get Help:[/bold]\n"
            "[cyan]$[/cyan] svcs [yellow]<command>[/yellow] --help       [dim]# Help for specific command[/dim]",
            title="[bold green]Examples[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(0, 2)
        )
        console.print(examples)
        console.print()

        # Footer
        console.print(
            "[dim]Version 1.2.0  |  "
            "More info: [/dim][cyan]https://github.com/muhammadsufiyanbaig/simple_vcs[/cyan]"
        )
        console.print()

        # Prevent Click from outputting its own help
        ctx.resilient_parsing = True

@click.group(cls=RichGroup)
@click.version_option(version="1.3.0", prog_name="SimpleVCS")
def main():
    """SimpleVCS - A beautiful and simple version control system"""
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