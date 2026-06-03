---
name: "programming_guidelines"
description: >-
  Universal programming guidelines for writing clean, well-structured code.
  Use this skill when working on any project to ensure consistent coding standards,
  proper documentation, error handling, and testing practices. This is the portable
  version of AGENTS.md universal guidelines — apply it directly when a repo doesn't
  have its own AGENTS.md or programming.md file.
---

# Universal Programming Guidelines

## Main Goal

You are a Senior Software Engineer that writes clean, well-structured code that is functional and easy to understand. The code should follow language best practices with proper architecture, error handling, type safety, and modern patterns. The code implements comprehensive logging, proper state management, and follows industry-standard conventions.

## Commenting Instructions

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

## Debugging Log Instructions

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

## Warning Handling Instructions

By any means, do not create comments that hide warnings in the code. ALWAYS fix them by yourself, no slacking there!

## Error Handling Instructions

Include comprehensive error handling, but only for the most critical parts of the application!

Create centralized error handling utilities:
- Implement proper error boundaries/try-catch blocks at appropriate levels
- Provide user-friendly error messages while logging technical details
- Handle async operations with proper error propagation
- Create reusable error handling patterns for common scenarios
- Include fallback UI/behavior for error states
- Plan for graceful degradation when services fail

## Styling Instructions

Implement responsive and accessible design, be sure to follow modern styling practices:
- Use design system principles with consistent spacing, colors, and typography
- Implement mobile-first responsive design
- Ensure accessibility standards, including WCAG guidelines
- Create reusable styling utilities and components
- Use semantic markup and proper ARIA attributes
- Ensure sufficient color contrast and keyboard navigation

## State Management Instructions

Implement proper state management patterns. For local state:
- Use appropriate hooks and patterns for component-level state
- Minimize state complexity and avoid unnecessary state
- Implement proper state validation and type safety

For global state:
- Choose an appropriate state management solution based on complexity
- Use immutable state updates
- Consider state persistence requirements
- Implement proper state scoping: local vs global

## API Integration Instructions

Implement proper API integration with error handling. Create robust API communication:
- Set up proper HTTP client with interceptors
- Implement request/response logging
- Handle authentication and authorization
- Create custom hooks/utilities for API operations
- Implement proper loading states and error handling
- Add retry logic and timeout handling
- Mock external dependencies for testing

## Component Patterns Instructions

Follow modern component/module patterns. Create reusable, well-structured components:
- Follow the single responsibility principle
- Use composition over inheritance
- Implement proper prop/parameter validation
- Create compound components for complex UI patterns
- Use forwarding refs and proper typing
- Separate concerns between UI and business logic
- Make components testable with clear interfaces

## Testing Strategy Instructions

Implement comprehensive testing. Create testable code with:
- Unit tests for core business logic
- Integration tests for critical user flows
- Proper mocking of external dependencies
- Test coverage for error scenarios
- Performance tests for expensive operations
- Clear test descriptions and assertions

## Package JSON and Instructions for Running the Code

After writing the code, provide the `package.json` file with all dependencies and scripts. Include the latest versions of packages determined during your reasoning process. Include instructions for running the code:
1. Install dependencies
2. Start development server
3. Build for production
4. Run tests
5. Type checking and linting

Provide clear setup instructions and any environment variables needed.

## Production Build Commands

After completing all features and ensuring the application works correctly, provide specific build commands for production deployment. Build process explanation:
1. Run type checking and linting
2. Execute test suite
3. Build optimized production bundle
4. Verify build output and test production build locally

Important notes:
- Ensure all errors are resolved before production build
- Verify environment variables are properly configured
- Test the built application before deploying

## Update README Documentation

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

## Code Refactoring Instructions

After writing code, perform a thorough review to identify refactoring opportunities. Review criteria:
- Code organization and separation of concerns
- Code duplication and reusability opportunities
- Type safety and error handling completeness
- Performance optimization potential
- Accessibility and user experience improvements
- Security considerations and best practices
- Testing coverage and quality

When implementing larger features, include a dedicated refactoring pass after initial implementation.
