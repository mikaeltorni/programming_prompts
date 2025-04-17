#!/usr/bin/env python3
"""
Copy Prompts To Projects

This script copies specific prompt files from a global prompts directory to 
multiple projects based on a JSON configuration file. It also ensures each project's
.gitignore contains the proper entry, and creates git commits as needed.

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

import os
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


def create_git_commit(project_path, message):
    """
    Create a git commit in the specified project directory.
    
    Parameters:
        project_path (str): Path to the project directory
        message (str): Commit message
        
    Returns:
        bool: True if the commit was successful, False otherwise
    """
    logger.debug(f"Creating git commit in {project_path} with message: {message}")
    try:
        subprocess.run(['git', '-C', project_path, 'add', '.'], check=True)
        subprocess.run(['git', '-C', project_path, 'commit', '-m', message], check=True)
        logger.info(f"Git commit created successfully in {project_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create git commit in {project_path}: {e}")
        return False


def copy_prompt_files(source_dir, dest_dir, prompt_files):
    """
    Copy specific prompt files from source directory to destination directory.
    
    Parameters:
        source_dir (Path): Source directory containing prompt files
        dest_dir (Path): Destination directory to copy files to
        prompt_files (list): List of prompt filenames to copy
        
    Returns:
        list: List of files that were actually copied
    """
    logger.debug(f"Copying prompt files to {dest_dir}")
    copied_files = []
    
    # Create destination directory if it doesn't exist
    if not dest_dir.exists():
        dest_dir.mkdir(parents=True, exist_ok=True)
    
    for prompt_file in prompt_files:
        source_file = source_dir / prompt_file
        dest_file = dest_dir / prompt_file
        
        if not source_file.exists():
            logger.warning(f"Source file not found: {source_file}")
            continue
            
        try:
            shutil.copy2(source_file, dest_file)
            logger.info(f"Copied: {prompt_file}")
            copied_files.append(prompt_file)
        except Exception as e:
            logger.error(f"Failed to copy {prompt_file}: {e}")
    
    return copied_files


def main():
    """
    Main function to process the configuration and copy prompt files.
    
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
            if gitignore_updated:
                create_git_commit(
                    repository_path, 
                    "chore: add .cursor/rules/global_prompts to .gitignore"
                )
        else:
            logger.info(f".gitignore in {repository_path} already has .cursor/rules/global_prompts entry.")
        
        # Target directory path
        target_dir = Path(repository_path) / ".cursor" / "rules" / "global_prompts"
        
        # Copy specified prompt files
        copied_files = copy_prompt_files(source_dir, target_dir, prompt_files)
        
        # Create commit if files were copied
        if copied_files:
            if len(copied_files) == 1:
                commit_message = f"chore: add prompt file {copied_files[0]}"
            else:
                commit_message = f"chore: add {len(copied_files)} prompt files"
            
            create_git_commit(repository_path, commit_message)
    
    logger.info("\nPrompt files have been copied to all specified projects.")


if __name__ == "__main__":
    main() 