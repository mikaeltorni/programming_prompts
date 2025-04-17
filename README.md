# Using the Prompt Symlink Script

The `copy_prompts.ps1` script allows you to create symbolic links from multiple projects to a single set of prompt files, ensuring all projects use the latest prompts.

## Prerequisites
- Windows PowerShell
- Administrator privileges

## Usage
1. Create a text file with the paths to your target projects, one per line:
   ```
   C:\Projects\gamedev\Fractavere
   C:\Projects\ai\software_prompt_engineering
   C:\Projects\ai\coding_tools
   ```

2. Run PowerShell as Administrator (right-click PowerShell and select "Run as Administrator")

3. Execute the script with:
   ```
   .\create_symlink_for_prompts.ps1 -PathsFile project_paths.txt
   ```

This will create symbolic links in all target projects pointing to the `.cursor\rules\global_prompts` directory in the current project. When you update prompts in the current project, all linked projects will automatically use the updated versions.

# TODO
- When creating new files, automatically make a new class for the contents inside that file
- Optimize docstring generation for the new files, especially that they are classes now, and the prompt is missing instructions for those

## Disclaimer

This software is provided under the MIT License on an **“as is”** basis, without warranties of any kind. To the maximum extent permitted by applicable law, the authors and copyright holders shall not be liable for any claims, damages, losses, or other liability arising from the use of this software.

You are solely responsible for determining whether this software is suitable, safe, lawful, and appropriate for your intended use. Unless explicitly stated otherwise, this project is general-purpose software and is not designed, tested, certified, or approved for safety-critical, medical, automotive, aviation, industrial-control, life-support, cybersecurity-critical, financial-critical, or other high-risk use cases.

The authors and copyright holders make no guarantees regarding security, reliability, availability, correctness, compliance, non-infringement, or fitness for any particular purpose.

This notice is intended to clarify the nature of the project and does not impose additional restrictions beyond the MIT License.
