import click
from .core import SimpleVCS

@click.group()
@click.version_option()
def main():
    """SimpleVCS - A simple version control system"""
    pass

@main.command()
@click.option('--path', default='.', help='Repository path')
def init(path):
    """Initialize a new repository"""
    vcs = SimpleVCS(path)
    vcs.init_repo()

@main.command()
@click.argument('files', nargs=-1, required=True)
def add(files):
    """Add files to staging area"""
    vcs = SimpleVCS()
    for file in files:
        vcs.add_file(file)

@main.command()
@click.option('-m', '--message', help='Commit message')
def commit(message):
    """Commit staged changes"""
    vcs = SimpleVCS()
    vcs.commit(message)

@main.command()
@click.option('--c1', type=int, help='First commit ID')
@click.option('--c2', type=int, help='Second commit ID')
def diff(c1, c2):
    """Show differences between commits"""
    vcs = SimpleVCS()
    vcs.show_diff(c1, c2)

@main.command()
@click.option('--limit', type=int, help='Limit number of commits to show')
def log(limit):
    """Show commit history"""
    vcs = SimpleVCS()
    vcs.show_log(limit)

@main.command()
def status():
    """Show repository status"""
    vcs = SimpleVCS()
    vcs.status()

if __name__ == '__main__':
    main