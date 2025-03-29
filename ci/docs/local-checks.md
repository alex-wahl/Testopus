# Local Code Quality Checks

This document provides detailed information about the local code quality checks implemented in the Testopus project.

## Overview

Testopus uses a combination of pre-commit hooks and a local CI script to ensure code quality standards are maintained throughout development. These tools run automatically at different stages of the development workflow to catch issues early and provide immediate feedback to developers.

## Pre-commit Hooks

[Pre-commit](https://pre-commit.com/) is a framework for managing and maintaining multi-language pre-commit hooks. These hooks run before each commit to catch issues early in the development process.

### Installed Hooks

The following hooks are configured in the `.pre-commit-config.yaml` file:

#### Basic File Checks
- **trailing-whitespace**: Trims trailing whitespace from files
- **end-of-file-fixer**: Ensures files end with a newline
- **check-yaml**: Validates YAML files
- **check-added-large-files**: Prevents committing large files

#### Python Code Quality
- **black**: Formats Python code according to Black's style guidelines
- **isort**: Sorts imports according to PEP 8 guidelines
- **flake8**: Lints Python code for errors and style issues
- **pylint**: Performs static code analysis
- **mypy**: Checks Python type annotations

### Installation

To set up the pre-commit hooks:

```bash
# Install pre-commit hooks globally (if not already installed)
pip install pre-commit

# Install hooks for the repository
pre-commit install

# Install pre-push hooks
pre-commit install --hook-type pre-push
```

### Usage

Pre-commit hooks run automatically whenever you attempt to commit changes, but you can also run them manually:

```bash
# Run all hooks on staged files
pre-commit run

# Run all hooks on all files
pre-commit run --all-files

# Run a specific hook on all files
pre-commit run black --all-files
```

### Hook Configuration

The hook configuration in `.pre-commit-config.yaml` can be customized based on project needs. The current configuration focuses on the `ci/scripts` directory, but this can be extended to other parts of the codebase as needed.

For example:

```yaml
-   repo: https://github.com/psf/black
    rev: 25.1.0
    hooks:
    -   id: black
        files: ^ci/scripts/  # This restricts the hook to the ci/scripts directory
```

## Local CI Check Script

The `local_ci_check.sh` script provides a comprehensive check of your code before pushing to the remote repository. This script combines multiple tools to verify code quality, run tests, and generate coverage reports.

### Script Components

The script performs the following checks:

1. **Environment Verification**
   - Checks if required tools are installed
   - Installs pre-commit hooks if not already installed

2. **Code Quality Checks**
   - **isort**: Checks and fixes import sorting
   - **black**: Verifies and applies code formatting
   - **flake8**: Performs linting for critical issues
   - **pylint**: Runs static analysis for common problems
   - **mypy**: Performs type checking

3. **Test Execution**
   - Runs unit tests using Python's unittest module
   - Generates test coverage reports
   - Displays coverage metrics

### Script Usage

```bash
# Run all checks
./local_ci_check.sh

# View the script output
./local_ci_check.sh | less
```

### Script Output

The script provides detailed output with emoji indicators:

- 🔍 Indicates a check or verification step
- ❌ Indicates a failed check
- ✅ Indicates a successful check or auto-fix

Example output:
```
🔍 Starting local CI checks...
📦 Installing pre-commit hooks...
🔄 Running import sorting (isort)...
🧹 Running code formatting (black)...
🔍 Running linting (flake8)...
🔍 Running static analysis (pylint)...
🔍 Running type checking (mypy)...
🧪 Running tests...
📊 Running tests with coverage...
✅ All checks passed! Your code is ready to be pushed.
```

## Workflow Integration

For the most efficient workflow, follow these steps:

1. **Development**
   - Make changes to the codebase
   - Run `local_ci_check.sh` to verify changes
   - Fix any issues reported by the script

2. **Committing Changes**
   - Stage your changes with `git add`
   - Commit your changes with `git commit`
   - Pre-commit hooks will run automatically
   - Fix any issues reported by the hooks

3. **Pushing Changes**
   - Push your changes with `git push`
   - Pre-push hooks will run automatically
   - CI/CD pipeline will run the same checks remotely

## Troubleshooting

### Common Issues

#### Pre-commit Hook Failures

If pre-commit hooks fail, the commit will be aborted. To resolve:

1. Review the error messages
2. Fix the reported issues
3. Stage the fixed files
4. Try committing again

To bypass hooks in exceptional cases:
```bash
git commit --no-verify -m "Commit message"
```

#### Local CI Script Failures

If the local CI script fails:

1. Review the output to identify which tool failed
2. Fix the reported issues
3. Run the script again to verify fixes

### Tool-Specific Issues

#### Black Formatting

If Black is reporting formatting issues:
```bash
# Format all Python files in the ci/scripts directory
black ci/scripts
```

#### Import Sorting

If isort is reporting import ordering issues:
```bash
# Fix imports in the ci/scripts directory
isort ci/scripts
```

#### Type Checking

If mypy is reporting type checking issues:
```bash
# Run mypy with more verbose output
mypy --show-error-context ci/scripts
```

## Adding New Checks

To add new checks to the pre-commit configuration:

1. Add the hook to `.pre-commit-config.yaml`
2. Run `pre-commit install` to update the hooks
3. Update the local CI script if needed
4. Document the new check in this file

## Conclusion

Local code quality checks are a critical part of the development workflow in Testopus. By catching issues early in the development process, these tools help maintain high code quality standards and reduce the likelihood of bugs in production. 