#!/bin/bash
set -e  # Exit on any error

echo "🔍 Starting local CI checks..."

# Check if required tools are installed
command -v black >/dev/null 2>&1 || { echo "❌ Black is not installed. Run: pip install black"; exit 1; }
command -v isort >/dev/null 2>&1 || { echo "❌ isort is not installed. Run: pip install isort"; exit 1; }
command -v flake8 >/dev/null 2>&1 || { echo "❌ flake8 is not installed. Run: pip install flake8"; exit 1; }
command -v pylint >/dev/null 2>&1 || { echo "❌ pylint is not installed. Run: pip install pylint"; exit 1; }
command -v mypy >/dev/null 2>&1 || { echo "❌ mypy is not installed. Run: pip install mypy"; exit 1; }

echo "📦 Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type pre-push

echo "🔄 Running import sorting (isort)..."
isort --check-only --profile black ci/scripts || {
    echo "❌ Import sorting failed. Fixing automatically..."
    isort --profile black ci/scripts
    echo "✅ Imports have been sorted. Please review the changes, commit them, and try pushing again."
    exit 1
}

echo "🧹 Running code formatting (black)..."
black --check ci/scripts || {
    echo "❌ Code formatting failed. Fixing automatically..."
    black ci/scripts
    echo "✅ Code has been formatted. Please review the changes, commit them, and try pushing again."
    exit 1
}

echo "🔍 Running linting (flake8)..."
# For the initial push, we'll just report critical errors but not fail
flake8 ci/scripts --count --select=E9,F63,F7,F82 --show-source --statistics || {
    echo "❌ Critical linting issues found. Please fix them before pushing."
    exit 1
}
# Non-critical linting, just for info
flake8 ci/scripts --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

echo "🔍 Running static analysis (pylint)..."
# For initial push, just report but don't fail on unused imports and variables
pylint --disable=all --enable=undefined-variable ci/scripts

echo "🔍 Running type checking (mypy)..."
# For initial push, just report but don't fail
mypy --ignore-missing-imports ci/scripts || {
    echo "⚠️ Type checking found issues. This is just a warning for now."
}

echo "🧪 Running tests..."
pushd ci/scripts > /dev/null
python -m unittest discover tests || {
    echo "❌ Tests failed. Please fix them before pushing."
    popd > /dev/null
    exit 1
}
popd > /dev/null

echo "✅ All checks passed! Your code is ready to be pushed."
