---
name: programming-guidelines
description: >-
  Mandatory general engineering workflow and coding standards. Use for every
  software task, including implementation, debugging, review, testing, and
  refactoring.
---

# General Programming Guidelines

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

## Planning and Execution Strategy

Before taking ANY action, create a clear execution plan:

1. **Analyze** the user's request and codebase to understand the scope
2. **Plan** the specific steps needed - list them as a numbered plan
3. **Execute** the plan step by step, verifying each step completes before moving to the next
4. **Stop** and reassess if you find yourself repeating tool calls without progress

Your plan must be explicit. Example plan format:
```
1. Read file A to understand current state
2. Read file B for context on X
3. Modify file A with changes Y
4. Verify changes work with test Z
```

**Stop immediately** and reconsider your approach if you're about to make a tool call you've already made in this session. Document what you learned from previous calls to avoid redundant exploration.

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
- Store every repository-generated log file under the repository root `.log/`
  directory. Logging code must create `.log/` before writing and must not place
  logs in the repository root, `data/`, `/tmp`, or scattered component folders.
- Add `.log/` to every repository's `.gitignore`; log files are runtime
  artifacts and must not be committed.

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

### Python Dependency Supply-Chain Protection

Apply this policy whenever creating a new project from zero or adding Python to
an existing project for the first time. Implement the protection in repository
code and documented setup commands so clean installations and CI use it by
default; do not rely on an agent remembering an optional flag.

- Delay newly published Python distributions for at least 24 hours. Every
  dependency resolution must calculate a rolling cutoff equal to the current
  UTC time minus 24 hours and pass it to `uv` with `--exclude-newer` or the
  equivalent `UV_EXCLUDE_NEWER` environment variable.
- Add a project-local wrapper or task that calculates the cutoff and is the
  documented entry point for `uv add`, lock, sync, install, update, and CI
  dependency operations. A fixed timestamp committed to `pyproject.toml` is
  insufficient because it does not remain a rolling 24-hour delay.
- Generate and commit `uv.lock`. Re-resolve an existing lock under the cutoff
  before treating the project as protected, and test that the wrapper supplies
  the cutoff to every command that can resolve or update packages.
- If regular Python tooling uses `pip`, pip must not resolve dependencies
  directly because it does not enforce this rolling publication-age policy.
  Produce a hash-bearing requirements file with `uv export` from the protected
  lock, then install it with `python -m pip install --require-hashes -r
  <requirements-file>`. Regenerate the export whenever the lock changes.
- Pin build-system requirements and all transitive dependencies through the
  same protected lock/export flow. Do not leave unconstrained bootstrap,
  development, test, lint, or build dependencies outside the policy.
- Bootstrap `uv` itself from a pinned release that has been public for at least
  24 hours, using an official distribution channel and checksum or signature
  verification where available. Do not execute an unpinned latest-release
  installer directly from the network.
- Document the emergency override, if one is added, as an explicit,
  auditable, opt-in action. It must never be the default local or CI path.

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
