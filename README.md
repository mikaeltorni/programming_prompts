# Copy Prompts To Projects

This utility copies specific prompt files from a central global prompts directory to multiple projects based on a JSON configuration file. It also automatically copies the `programming_guidelines` folder to all projects, ensures each project's `.gitignore` contains the proper entry, and creates git commits as needed.

## Features

- Copies specific prompt files to multiple repositories
- Provides reusable Codex plugins under `plugins/`:
  - `general-programming-guidelines` packages the canonical `programming.md`.
  - `commit-guidelines` packages the cautious Git commit workflow from
    `skills/commit/SKILL.md`.
- **Always copies the `programming_guidelines` folder to all projects**
- Updates `.gitignore` files to include `.cursor/rules/global_prompts`
- Creates appropriate git commits for each repository
- Provides detailed logging under the repository-local `.log/` directory
- Supports custom configuration through JSON

## Requirements

- Python 3.6 or higher
- Git must be installed and configured

## Installation

1. Clone or download this repository
2. Ensure your `.cursor/rules/global_prompts` directory contains the prompt files you want to copy

## Usage

1. Create a JSON configuration file (see `sample_config.json` for an example) that defines:
   - Repository paths
   - List of prompt files for each repository

2. Run the script:
   ```
   python copy_prompts_to_projects.py your_config.json
   ```

## Codex Plugins

Validate the plugins before installation:

```bash
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/general-programming-guidelines
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/commit-guidelines
```

The personal Codex marketplace installs these as
`general-programming-guidelines@personal` and `commit-guidelines@personal`.
Confirm their status with `codex plugin list`.

The programming guidelines require every repository-generated file log to live
under `.log/`, and every repository must ignore `.log/`.

## Configuration File Format

The configuration file should be a JSON array of objects, where each object represents a repository with:
- `repository_path`: The path to the repository directory
- `prompts`: Array of prompt filenames to copy to that repository

Example:
```json
[
  {
    "repository_path": "C:\\folder\\example1",
    "prompts": [
      "python_programming.mdc",
      "javascript_programming.mdc"
    ]
  },
  {
    "repository_path": "C:\\folder\\example2",
    "prompts": [
      "python_programming.mdc"
    ]
  }
]
```

## How It Works

1. For each repository in the configuration:
   - Checks if `.gitignore` already has the `.cursor/rules/global_prompts` entry
   - If not, adds it and creates a commit
   - **Always copies the entire `programming_guidelines` folder** from the source directory
   - Copies each specified prompt file to the repository's `.cursor/rules/global_prompts` directory
   - Logs all operations performed

2. Only performs operations when necessary:
   - Skips repositories with invalid paths
   - Skips repositories with no prompt files specified
   - Only updates `.gitignore` if needed
   - Always refreshes the `programming_guidelines` folder to ensure it's up to date
   - Only copies prompt files that have changed or don't exist

3. Directory Management:
   - Creates the `.cursor/rules/global_prompts` directory if it doesn't exist
   - Completely replaces the `programming_guidelines` folder to ensure consistency
   - Compares file contents to avoid unnecessary file operations

# TODO
- When creating new files, automatically make a new class for the contents inside that file
- Optimize docstring generation for the new files, especially that they are classes now, and the prompt is missing instructions for those

## Disclaimer

This software is provided under the MIT License on an **“as is”** basis, without warranties of any kind. To the maximum extent permitted by applicable law, the authors and copyright holders shall not be liable for any claims, damages, losses, or other liability arising from the use of this software.

You are solely responsible for determining whether this software is suitable, safe, lawful, and appropriate for your intended use. Unless explicitly stated otherwise, this project is general-purpose software and is not designed, tested, certified, or approved for safety-critical, medical, automotive, aviation, industrial-control, life-support, cybersecurity-critical, financial-critical, or other high-risk use cases.

The authors and copyright holders make no guarantees regarding security, reliability, availability, correctness, compliance, non-infringement, or fitness for any particular purpose.

This notice is intended to clarify the nature of the project and does not impose additional restrictions beyond the MIT License.
