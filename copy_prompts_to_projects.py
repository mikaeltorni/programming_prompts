#!/usr/bin/env python3
"""
Copy Prompts To Projects

This script copies specific prompt files from a global prompts directory to 
multiple projects based on a JSON configuration file. It also ensures each project's
.gitignore contains the proper entry, and creates git commits as needed.

Additionally, it always copies the programming_guidelines folder to each project.

Usage:
    python copy_prompts_to_projects.py config.json

Requirements:
    - Git must be installed and configured

Arguments:
    config_file: Path to a JSON configuration file with the format:
    [
      {
        "repository_path": "C:\\Projects\\example",
        "prompts": ["prompt1.md", "prompt2.md"]
      }
    ]
"""

import sys
import json
import shutil
import subprocess
from pathlib import Path
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def check_gitignore(project_path):
    """
    Check if .gitignore in the project has .cursor/rules/global_prompts entry.
    
    Parameters:
        project_path (str): Path to the project directory
        
    Returns:
        bool: True if the entry exists, False otherwise
    """
    logger.debug(f"Checking .gitignore in {project_path}")
    gitignore_path = Path(project_path) / '.gitignore'
    
    if not gitignore_path.exists():
        return False
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
        
    return '.cursor/rules/global_prompts' in content


def update_gitignore(project_path):
    """
    Add .cursor/rules/global_prompts to the .gitignore file.
    
    Parameters:
        project_path (str): Path to the project directory
        
    Returns:
        bool: True if the file was updated, False if it already had the entry
    """
    logger.debug(f"Updating .gitignore in {project_path}")
    gitignore_path = Path(project_path) / '.gitignore'
    
    entry = '.cursor/rules/global_prompts'
    updated = False
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        if entry not in content:
            with open(gitignore_path, 'a') as f:
                if not content.endswith('\n'):
                    f.write('\n')
                f.write(f'{entry}\n')
            updated = True
    else:
        with open(gitignore_path, 'w') as f:
            f.write(f'{entry}\n')
        updated = True
    
    return updated


def has_git_changes(project_path):
    """
    Check if the repository has uncommitted changes.
    
    Parameters:
        project_path (str): Path to the project directory
        
    Returns:
        bool: True if there are uncommitted changes, False otherwise
    """
    try:
        # Use git status --porcelain to get a machine-readable output
        result = subprocess.run(
            ['git', '-C', project_path, 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=True
        )
        # If the output is not empty, there are changes
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        logger.error(f"Failed to check git status in {project_path}")
        return False


def create_git_commit(project_path, message):
    """
    Create a git commit in the specified project directory if there are changes.
    
    Parameters:
        project_path (str): Path to the project directory
        message (str): Commit message
        
    Returns:
        bool: True if the commit was successful, False otherwise
    """
    logger.debug(f"Creating git commit in {project_path} with message: {message}")
    
    # Check if there are changes to commit
    if not has_git_changes(project_path):
        logger.info(f"No changes to commit in {project_path}")
        return False
    
    try:
        subprocess.run(['git', '-C', project_path, 'add', '.gitignore'], check=True)
        subprocess.run(['git', '-C', project_path, 'commit', '-m', message], check=True)
        logger.info(f"Git commit created successfully in {project_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create git commit in {project_path}: {e}")
        return False


def copy_directory(source_dir, dest_dir, dir_name):
    """
    Copy a directory from source to destination, comparing contents to avoid unnecessary copies.
    
    Parameters:
        source_dir (Path): Source directory containing the folder to copy
        dest_dir (Path): Destination directory to copy folder to
        dir_name (str): Name of the directory to copy
        
    Returns:
        bool: True if the directory was copied or updated, False otherwise
    """
    logger.debug(f"Copying directory {dir_name} to {dest_dir}")
    
    source_folder = source_dir / dir_name
    dest_folder = dest_dir / dir_name
    
    if not source_folder.exists():
        logger.warning(f"Source directory not found: {source_folder}")
        return False
    
    if not source_folder.is_dir():
        logger.warning(f"Source path is not a directory: {source_folder}")
        return False
    
    # Create destination directory if it doesn't exist
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if destination folder exists
    if dest_folder.exists():
        # Remove existing folder to ensure clean copy
        try:
            shutil.rmtree(dest_folder)
            logger.debug(f"Removed existing directory: {dest_folder}")
        except Exception as e:
            logger.error(f"Failed to remove existing directory {dest_folder}: {e}")
            return False
    
    try:
        shutil.copytree(source_folder, dest_folder)
        logger.info(f"Copied directory: {dir_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to copy directory {dir_name}: {e}")
        return False


def copy_prompt_files(source_dir, dest_dir, prompt_files):
    """
    Copy specific prompt files from source directory to destination directory.
    
    Parameters:
        source_dir (Path): Source directory containing prompt files
        dest_dir (Path): Destination directory to copy files to
        prompt_files (list): List of prompt filenames to copy (may include subdirectories)
        
    Returns:
        list: List of files that were actually copied
    """
    logger.debug(f"Copying prompt files to {dest_dir}")
    logger.info(f"Source directory: {source_dir}")
    logger.info(f"Destination directory: {dest_dir}")
    logger.info(f"Files to copy: {prompt_files}")
    
    copied_files = []
    
    # Create destination directory if it doesn't exist
    if not dest_dir.exists():
        dest_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created destination directory: {dest_dir}")
    
    for prompt_file in prompt_files:
        logger.info(f"Processing file: {prompt_file}")
        
        # Handle both forward slashes and backslashes in file paths
        normalized_path = prompt_file.replace('\\', '/')
        source_file = source_dir / normalized_path
        dest_file = dest_dir / normalized_path
        
        logger.info(f"  Source path: {source_file}")
        logger.info(f"  Destination path: {dest_file}")
        logger.info(f"  Source exists: {source_file.exists()}")
        
        if not source_file.exists():
            logger.warning(f"Source file not found: {source_file}")
            continue
        
        # Create parent directories for the destination file if they don't exist
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"  Ensured destination directory exists: {dest_file.parent}")
        
        # Check if the file exists and is identical
        if dest_file.exists():
            logger.info(f"  Destination file exists, comparing contents...")
            try:
                # Compare file contents to see if they are identical
                with open(source_file, 'rb') as src, open(dest_file, 'rb') as dst:
                    src_content = src.read()
                    dst_content = dst.read()
                    if src_content == dst_content:
                        logger.info(f"File already exists and is identical: {prompt_file}")
                        continue
                    else:
                        logger.info(f"File exists but content is different, will overwrite: {prompt_file}")
            except Exception as e:
                # If there's an error comparing, just copy the file
                logger.warning(f"Error comparing files, will copy anyway: {e}")
                pass
            
        try:
            shutil.copy2(source_file, dest_file)
            logger.info(f"Successfully copied: {prompt_file}")
            copied_files.append(prompt_file)
        except Exception as e:
            logger.error(f"Failed to copy {prompt_file}: {e}")
    
    logger.info(f"Copy operation completed. Files copied: {len(copied_files)}")
    return copied_files


def main():
    """
    Main function to process the configuration and copy prompt files and directories.
    
    Parameters:
        None
        
    Returns:
        None
    """
    if len(sys.argv) != 2:
        logger.error("Usage: python copy_prompts_to_projects.py config.json")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    # Check if config file exists
    if not Path(config_file).exists():
        logger.error(f"Config file not found: {config_file}")
        sys.exit(1)
    
    # Read configuration
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        sys.exit(1)
    
    # Source directory in the current project
    script_dir = Path(__file__).resolve().parent
    source_dir = script_dir / ".cursor" / "rules" / "global_prompts"
    source_dir = source_dir.resolve()
    
    # Check if source directory exists
    if not source_dir.exists():
        logger.error(f"Source directory not found: {source_dir}")
        sys.exit(1)
    
    for repo_config in config:
        repository_path = repo_config.get("repository_path")
        prompt_files = repo_config.get("prompts", [])
        
        if not repository_path or not Path(repository_path).exists():
            logger.warning(f"Repository path not found or invalid: {repository_path}")
            continue
        
        if not prompt_files:
            logger.warning(f"No prompt files specified for repository: {repository_path}")
            continue
        
        logger.info(f"\nProcessing repository: {repository_path}")
        
        # Check and update .gitignore if needed
        gitignore_updated = False
        if not check_gitignore(repository_path):
            gitignore_updated = update_gitignore(repository_path)
            if gitignore_updated and has_git_changes(repository_path):
                create_git_commit(
                    repository_path, 
                    "chore: add .cursor/rules/global_prompts to .gitignore"
                )
        else:
            logger.info(f".gitignore in {repository_path} already has .cursor/rules/global_prompts entry.")
        
        # Target directory path
        target_dir = Path(repository_path) / ".cursor" / "rules" / "global_prompts"
        
        # Always copy the programming_guidelines directory
        programming_guidelines_copied = copy_directory(source_dir, target_dir, "programming_guidelines")
        if programming_guidelines_copied:
            logger.info(f"Updated programming_guidelines directory in {repository_path}")
        
        # Copy specified prompt files
        copied_files = copy_prompt_files(source_dir, target_dir, prompt_files)
        
        # No need to commit the copied files since they're gitignored
        # But we'll log the information about what was copied
        if copied_files:
            if len(copied_files) == 1:
                logger.info(f"Added prompt file {copied_files[0]} to {repository_path}")
            else:
                logger.info(f"Added {len(copied_files)} prompt files to {repository_path}")
    
    logger.info("\nPrompt files and programming guidelines have been copied to all specified projects.")


if __name__ == "__main__":
    main() 