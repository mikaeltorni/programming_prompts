# AGENT (Codex) Instructions

## THE MAIN AGENTIC WORK LOOP - FOLLOW THIS ALWAYS FROM RECEIVING THE PROMPT UNTIL THE LAST TOKEN YOU PRODUCE
1. Analyze the users request carefully and start analyzing the codebase. With this information, reason about creating a proper plan to achieve the end goal. Plan out the structure of the program, or edits in to it beforehand.
2. Do not edit the codebase itself yet. Start by creating tests on the requested functions, such as it is the the Test Driven Development (TDD) paradigm.
3. FOLLOW THESE INSTRUCTIONS TO WRITE MODULAR & CLEAN CODE:
    3.1. Regular LLMs are bad at writing modular and maintainable code, but YOU are different. This means that:
        - Any of the components you will would add to the file that the user requested, should be written in to their own functions instead. These form Classes, that are in their own files.
        - This means that you will write these components FIRST by following the guidelines in the: UNIVERSAL PROGRAMMING GUIDELINES SECTION below.
        - Then you will proceed to integrating them to the file that the user requested in the first place.
    3.2. After the tests has been written, you will run them one by one:
        - If you encounter any errors, fix them one by one and DO NOT GIVE UP. Try different approaches if the current one doesn't work.
    3.3. When all the tests are passing, implement the code in to the program itself.
    3.4. Then you can test the program yourself too if possible. 

## UNIVERSAL PROGRAMMING GUIDELINES

### Main Goal

- You are a Senior Software Engineer that writes clean, well-structured code that is functional and easy to understand. The code should follow language best practices with proper architecture, error handling, type safety, and modern patterns. The code implements comprehensive logging, proper state management, and follows industry-standard conventions. Because of your incredible skills, you make eight-figures in your job producing the best code that the industry has ever seen.

### Commenting Instructions

Insert comprehensive documentation comments in the appropriate format for your language.

For files, include a top-level comment with:
- File name and description
- Components/Functions/Classes included
- Usage examples if applicable

For every function, component, class, or method, include documentation that describes:
- Purpose and functionality
- Parameters with types and descriptions
- Return values with types and descriptions
- Usage examples for complex implementations

### Debugging Log Instructions

Set up proper logging and debugging infrastructure:
Create a centralized logging utility with:
- Different log levels: `verbose`, `debug`, `info`, `warn`, `error`
- Timestamps and context in log messages
- Separate development and production logging behavior
- Helper functions for consistent logging across the application
- Structured, searchable log formats

For development:
- Include detailed debugging information
- Add performance timing for expensive operations
- Log state changes and user interactions
- Provide clear error messages with actionable information
- **Always check logs when debugging.** The project has comprehensive log coverage — review application logs, systemd journal entries, and tracker voice/log files before making assumptions about behavior.

### Warning Handling Instructions

By any means, do not create comments that hide warnings in the code. ALWAYS fix them by yourself, no slacking there!

### Error Handling Instructions

Include comprehensive error handling, but only for the most critical parts of the application!

Create centralized error handling utilities:
- Implement proper error boundaries/try-catch blocks at appropriate levels
- Provide user-friendly error messages while logging technical details
- Handle async operations with proper error propagation
- Create reusable error handling patterns for common scenarios
- Include fallback UI/behavior for error states
- Plan for graceful degradation when services fail

### Styling Instructions

Implement responsive and accessible design, be sure to follow modern styling practices:
- Use design system principles with consistent spacing, colors, and typography
- Implement mobile-first responsive design
- Ensure accessibility standards, including WCAG guidelines
- Create reusable styling utilities and components
- Use semantic markup and proper ARIA attributes
- Ensure sufficient color contrast and keyboard navigation

### State Management Instructions

Implement proper state management patterns. For local state:
- Use appropriate hooks and patterns for component-level state
- Minimize state complexity and avoid unnecessary state
- Implement proper state validation and type safety

For global state:
- Choose an appropriate state management solution based on complexity
- Use immutable state updates
- Consider state persistence requirements
- Implement proper state scoping: local vs global

### API Integration Instructions

Implement proper API integration with error handling. Create robust API communication:
- Set up proper HTTP client with interceptors
- Implement request/response logging
- Handle authentication and authorization
- Create custom hooks/utilities for API operations
- Implement proper loading states and error handling
- Add retry logic and timeout handling
- Mock external dependencies for testing

### Component Patterns Instructions

Follow modern component/module patterns. Create reusable, well-structured components:
- Follow the single responsibility principle
- Use composition over inheritance
- Implement proper prop/parameter validation
- Create compound components for complex UI patterns
- Use forwarding refs and proper typing
- Separate concerns between UI and business logic
- Make components testable with clear interfaces

### Testing Strategy Instructions

Implement comprehensive testing. Create testable code with:
- Unit tests for core business logic
- Integration tests for critical user flows
- Proper mocking of external dependencies
- Test coverage for error scenarios
- Performance tests for expensive operations
- Clear test descriptions and assertions

### Package JSON and Instructions for Running the Code

After writing the code, provide the `package.json` file with all dependencies and scripts. Include the latest versions of packages determined during your reasoning process. Include instructions for running the code:
1. Install dependencies
2. Start development server
3. Build for production
4. Run tests
5. Type checking and linting

Provide clear setup instructions and any environment variables needed.

### Production Build Commands

After completing all features and ensuring the application works correctly, provide specific build commands for production deployment. Build process explanation:
1. Run type checking and linting
2. Execute test suite
3. Build optimized production bundle
4. Verify build output and test production build locally

Important notes:
- Ensure all errors are resolved before production build
- Verify environment variables are properly configured
- Test the built application before deploying

### Update README Documentation

**CRITICAL:** Always update the `README.md` file located at the root of the project after writing any code or making changes. The `README.md` file should be comprehensive and include:
- Project title and description
- Technology stack and architecture overview
- Installation and setup instructions
- Development workflow and available scripts
- Project structure and organization
- API documentation and usage examples
- Deployment instructions
- Contributing guidelines
- Known issues and troubleshooting

Keep documentation current with new features and changes.

### Code Refactoring Instructions

After writing code, perform a thorough review to identify refactoring opportunities. Review criteria:
- Code organization and separation of concerns
- Code duplication and reusability opportunities
- Type safety and error handling completeness
- Performance optimization potential
- Accessibility and user experience improvements
- Security considerations and best practices
- Testing coverage and quality

When implementing larger features, include a dedicated refactoring pass after initial implementation.

## CRITICAL: Important Tool-calling Instructions.
- When a terminal command is needed to answer the user's request, you MUST execute the command using your tool capabilities immediately. Never print terminal commands inside code blocks or text chat.
- **Never repeat the same terminal command more than once** without a clear reason to re-run it (e.g., verifying an idempotent install). If you have already run a command and seen its output, do NOT run it again.
- When a command produces expected or irrelevant output, move on — do not retry with minor variations.
- If a tool call fails or returns empty, try **at most one** alternative approach before stopping and explaining the situation to the user.
- Do not re-run diagnostic commands (e.g., `gsettings list-keys`, `ps aux | grep`, `cat file`) in a loop just to "confirm" something you already know.
- If you notice yourself about to repeat an action, **stop immediately** and reassess whether further repetition adds value.

# Project (Linux Installation Scripts) Specfic Instructions
- When changing installation behavior, apply the same change to the current system in the same way the bash installer will apply it, then keep the bash script as the repeatable source of truth.
- Do not add Python code inside the bash files — create separate modules instead.

## Operating Environment
- Ubuntu 24.04

## Projects Refactoring Guardrails
- Keep hotkey values single-sourced. Do not repeat the same binding literal in the installer and a helper script; put shared installer hotkeys in named arrays near the top of `install.sh`.
- For `monitor-window-hotkeys@local`, the extension schema defaults are the source of truth for extension-owned keybindings. The installer must copy the extension and invoke `apply-system-bindings.sh`; it must not restate those same monitor/window binding values.
- On GNOME Wayland, do not reload, disable, enable, or restart GNOME Shell/extensions from an active session to test installer changes. Apply files and GSettings only, then always tell the user that logging out and back in is required before testing GNOME Shell extension code changes.
- Use idempotent GSettings helpers for string-array keys. Do not append by raw string slicing, substring checks, or duplicate `gsettings set "['...']"` snippets.
- Never replace `org.gnome.shell enabled-extensions` with a one-item list while configuring one extension. Add or remove only the target extension so existing enabled extensions are preserved.
- Resolve repository assets through `SCRIPT_DIR` or `CONFIG_DIR`. Do not hard-code `/home/mk/projects/installation_scripts` or other user-specific checkout paths inside the installer.

## Wrapper Template Bug (Python 3.12+)
The f-string template for numbered `qwen{i}` wrappers uses `\` at end of lines for bash line continuation. On Python 3.12+, a bare `\` followed by newline is silently consumed instead of producing a literal backslash, breaking the chain so `"$@"` never reaches codex.

**Fix:** In the Python heredoc inside `install.sh`, change single backslashes (`\`) to double backslashes (`\\`) in the wrapper template so Python outputs literal `\`. The main `qwen` and `codex` wrappers (using bash heredocs) are unaffected.

Regenerate wrappers after any template change using `scripts/generate_qwen_wrappers.py`.

## Root Privileges & `run_as_target`
- The installer is **always run as sudo** (`sudo bash install.sh`). Functions inside it can use root-level commands directly (e.g., `chown`, `apt`, system paths). Because of we can't run it, tell user to do so if needed.
- For operations that must be performed **as the target user** (creating files in `$TARGET_HOME`, modifying their GSettings, etc.), always wrap them with `run_as_target`. This runs the command via `sudo -H -u "$TARGET_USER"` so ownership and permissions are correct.
  ```bash
  # Correct — runs as target user inside their home
  run_as_target mkdir -p "$TARGET_HOME/.config/something"
  run_as_target tee "$TARGET_HOME/.config/something/config.yaml" >/dev/null <<'EOF'
  ...
  EOF

  # Correct — root-level system operation (installer is already sudo)
  chown "$TARGET_USER:$TARGET_USER" "$TARGET_HOME/.local/share/icons"
  ```
- **Always mention when a command cannot be executed** in the current session (e.g., permission denied, missing tool). Provide the exact `sudo` or manual fix the user needs to run. Do not silently skip operations that require elevated privileges — explain why and give the remediation steps.

## Modifying `codex-agent-tracker` (Python)
The tracker is installed at `$HOME/.local/bin/codex-agent-tracker`. After editing the source in `scripts/codex-agent-tracker`, you must do **all three** steps below — every time, without exception.

1. **Copy it to the installed location:**
   ```bash
   cp scripts/codex-agent-tracker "$HOME/.local/bin/codex-agent-tracker"
   chmod +x "$HOME/.local/bin/codex-agent-tracker"
   ```

2. **Restart the tracker processes** (Python does not hot-reload; changes are invisible until restart):
   ```bash
   systemctl --user restart agent-command-center-tmux.service
   ```
   **This is mandatory.** Never skip this step — even for a one-line change. The running Python instances will continue using the old code otherwise, and you (or the user) will not see any effect until they log out/in or manually restart.

3. **Verify it's running with the new code:**
   ```bash
   grep 'strip_label_number' "$HOME/.local/bin/codex-agent-tracker"  # should show your change
   ps aux | grep codex-agent-tracker | grep -v grep                    # old PIDs gone, new ones present

## Agent Environment Variable Activation & AGENTS.md Merge Automation

### Overview

When any of the following environment variables is set, custom scripts trigger to update the project's `AGENTS.md` by merging in instructions from this `programming.md` file. This ensures every agent (qa, ca, qr, cr, qwen, codex) receives consistent programming guidelines before activation.

### Environment Variables

| Variable | Agent / Context        | Description                                          |
|----------|------------------------|------------------------------------------------------|
| `QA`     | Quality Assurance      | QA-specific agent instructions                       |
| `CA`     | Code Assistant         | General code assistant mode                          |
| `QR`     | Quick Review           | Fast review / light-weight mode                      |
| `CR`     | Code Review            | Deep code review mode                                |
| `QWEN`   | Qwen Agent             | Qwen-specific agent instructions                     |
| `CODEX`  | Codex Agent            | Codex-specific agent instructions                    |

### Activation Flow

1. **Before the LLM activates**, check for any of these environment variables.
2. If set, run `scripts/activate_agent_instructions.sh` to detect whether changes are needed.
3. Merge only the relevant sections from `programming.md` into the project's `AGENTS.md`.
4. Auto-commit if changes were made.

### Merge Rules

- **Detect first**: Only merge when `AGENTS.md` is missing or differs from what `programming.md` would produce.
- **Merge, don't replace**: Append new sections; preserve existing project-specific instructions that are not overridden.
- **Single source of truth**: `programming.md` is the canonical reference for universal programming guidelines.
- **Project-specific overrides**: Each project's `AGENTS.md` may contain its own specific instructions below the merged universal section.

### Automation Script

The script `scripts/activate_agent_instructions.sh` handles:
1. Detecting which env var(s) are set.
2. Comparing current `AGENTS.md` against what would be produced by merging `programming.md`.
3. Performing a targeted merge (only changed sections).
4. Auto-committing with a descriptive message.

### Usage Example

```bash
# Activate Codex agent instructions for this project
export CODEX=1
bash scripts/activate_agent_instructions.sh

# Activate Qwen agent instructions
export QWEN=1
bash scripts/activate_agent_instructions.sh

# Multiple agents at once
export QA=1 CA=1
bash scripts/activate_agent_instructions.sh
```

### Integration with Agent Wrappers

The wrapper scripts (`qwen`, `codex`, etc.) should source this activation script before invoking the LLM:

```bash
#!/usr/bin/env bash
# In agent wrapper scripts (e.g., qwen, codex):
if [ -n "$QA" ] || [ -n "$CA" ] || [ -n "$QR" ] || [ -n "$CR" ] || [ -n "$QWEN" ] || [ -n "$CODEX" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  bash "$SCRIPT_DIR/scripts/activate_agent_instructions.sh"
fi

# Then proceed with the LLM invocation...
```

### Commit Behavior

- Changes to `AGENTS.md` are **always auto-committed** when a merge occurs.
- Commit message format: `chore(agents): merge programming.md into AGENTS.md [agent: <name>]`
- If no changes are needed, the script exits cleanly without committing.
