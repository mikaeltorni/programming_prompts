"""
Create Symlink For Prompts

This script creates symbolic links for the .cursor/rules/global_prompts directory
across multiple projects specified in a paths file. It also checks if the .gitignore
file in each project contains the '.cursor/rules/global_prompts' entry and adds a 
git commit if needed.

Usage:
    python create_symlink_for_prompts.py paths_file.txt

Requirements:
    - Must be run with administrator privileges on Windows
    - Git must be installed and configured

Arguments:
    paths_file: Path to a text file containing target project paths (one per line)
"""

import os
import sys
import platform
import ctypes
import subprocess
from pathlib import Path


def is_admin():
    """Check if the script is running with administrator privileges."""
    if platform.system() == 'Windows':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        # On Unix systems, check if running as root (uid 0)
        return os.geteuid() == 0


def check_gitignore(project_path):
    """Check if .gitignore in the project has .cursor/rules/global_prompts entry."""
    gitignore_path = Path(project_path) / '.gitignore'
    
    if not gitignore_path.exists():
        return False
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
        
    return '.cursor/rules/global_prompts' in content


def update_gitignore(project_path):
    """Add .cursor/rules/global_prompts to the .gitignore file."""
    gitignore_path = Path(project_path) / '.gitignore'
    
    entry = '.cursor/rules/global_prompts'
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        if entry not in content:
            with open(gitignore_path, 'a') as f:
                if not content.endswith('\n'):
                    f.write('\n')
                f.write(f'{entry}\n')
    else:
        with open(gitignore_path, 'w') as f:
            f.write(f'{entry}\n')


def create_git_commit(project_path):
    """Create a git commit for adding .cursor/rules/global_prompts to .gitignore."""
    try:
        subprocess.run(['git', '-C', project_path, 'add', '.gitignore'], check=True)
        subprocess.run([
            'git', '-C', project_path, 'commit', '-m', 
            'chore: add .cursor/rules/global_prompts to the project with them being in .gitignore'
        ], check=True)
        print(f"Git commit created successfully in {project_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create git commit in {project_path}: {e}")


def create_symlink(source_dir, target_dir):
    """Create a symbolic link from target_dir to source_dir."""
    target_path = Path(target_dir)
    
    # Remove existing directory or symlink if it exists
    if target_path.exists() or target_path.is_symlink():
        print(f"Removing existing directory/link: {target_path}")
        if target_path.is_dir() and not target_path.is_symlink():
            import shutil
            shutil.rmtree(target_path)
        else:
            target_path.unlink()
    
    # Create symbolic link
    print(f"Creating symbolic link at: {target_path}")
    try:
        target_path.symlink_to(source_dir, target_is_directory=True)
        print("Symbolic link created successfully.")
    except Exception as e:
        print(f"Failed to create symbolic link: {e}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python create_symlink_for_prompts.py paths_file.txt")
        sys.exit(1)
    
    paths_file = sys.argv[1]
    
    # Check if running as administrator
    if not is_admin() and platform.system() == 'Windows':
        print("Warning: This script requires administrator privileges to create symbolic links.")
        print("Please run as Administrator and try again.")
        sys.exit(1)
    
    # Source directory in the current project (absolute path)
    script_dir = Path(__file__).resolve().parent
    source_dir = script_dir / ".cursor" / "rules" / "global_prompts"
    source_dir = source_dir.resolve()
    
    # Check if source directory exists
    if not source_dir.exists():
        print(f"Error: Source directory not found: {source_dir}")
        sys.exit(1)
    
    # Check if paths file exists
    if not Path(paths_file).exists():
        print(f"Error: Paths file not found: {paths_file}")
        sys.exit(1)
    
    # Read target project paths from the file
    with open(paths_file, 'r') as f:
        target_paths = [line.strip() for line in f if line.strip()]
    
    for project_path in target_paths:
        print(f"\nProcessing project: {project_path}")
        
        # Check if .gitignore already has the entry
        if check_gitignore(project_path):
            print(f"Info: .gitignore in {project_path} already has .cursor/rules/global_prompts entry. Skipping this repo.")
            continue
        
        # Create parent directory path (.cursor/rules)
        parent_dir = Path(project_path) / ".cursor" / "rules"
        
        # Create the parent directory if it doesn't exist
        if not parent_dir.exists():
            print(f"Creating directory: {parent_dir}")
            parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Target directory path
        target_dir = Path(project_path) / ".cursor" / "rules" / "global_prompts"
        
        # Create symbolic link
        create_symlink(source_dir, target_dir)
        
        # Update .gitignore and create git commit
        update_gitignore(project_path)
        create_git_commit(project_path)
    
    print("\nSymbolic links have been created for all specified projects.")


if __name__ == "__main__":
    main() 