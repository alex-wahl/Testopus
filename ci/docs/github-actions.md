# GitHub Actions Workflow Documentation

This document provides detailed information about the GitHub Actions workflow used in the Testopus project.

## Overview

The main workflow file is located at `.github/workflows/test.yml` and is responsible for:

1. Running automated tests in a Docker environment
2. Generating and customizing test reports
3. Publishing reports to GitHub Pages
4. Providing feedback on Pull Requests

## Workflow Triggers

The workflow can be triggered in three ways:

```yaml
on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:
    inputs:
      test_suite:
        description: 'Test suite to run'
        required: false
        default: 'all'
        type: choice
        options:
          - all
          - ui
          - api
          - internal
      debug_mode:
        description: 'Enable debug output'
        required: false
        default: false
        type: boolean
      custom_flags:
        description: 'Additional test flags'
        required: false
        type: string
```

- **Push Trigger**: Runs on any push to main or master branches
- **Pull Request Trigger**: Runs when PRs are opened against main or master
- **Manual Trigger**: Can be manually triggered from GitHub UI with configurable options:
  - `test_suite`: Choose which test suite to run
  - `debug_mode`: Enable verbose logging
  - `custom_flags`: Add custom pytest flags

## Permissions

The workflow defines specific permissions to follow the principle of least privilege:

```yaml
permissions:
  contents: write
  pages: write
  id-token: write
  checks: write
  pull-requests: write
```

These permissions allow the workflow to:
- Write to repository contents (for report deployment)
- Deploy to GitHub Pages
- Create check runs for test results
- Comment on pull requests

## Concurrency Control

The workflow uses concurrency control to manage multiple runs:

```yaml
concurrency:
  group: "pages"
  cancel-in-progress: false
```

This ensures that only one report deployment happens at a time, but doesn't cancel in-progress runs.

## Test Job

The main job in the workflow is called `test` and performs the following steps:

### 1. Environment Setup

```yaml
- uses: actions/checkout@v4
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'
- name: Install Hatch
  run: pip install hatch
- name: Install CI dependencies
  run: pip install -r ci/requirements.txt
```

These steps:
- Check out the repository code
- Set up Python 3.12
- Install Hatch package manager
- Install CI dependencies from requirements.txt

### 2. Directory Preparation

```yaml
- name: Prepare directories
  run: |
    mkdir -p reports/allure-results
    mkdir -p reports/html
    mkdir -p reports/junit
    mkdir -p reports/screenshots
    mkdir -p reports/allure-report
    chmod -R 777 reports
    echo "Listing test directories:"
    find tests -type f -name "test_*.py" | sort
```

This step creates required directories for storing test reports and outputs.

### 3. Docker Setup

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
- name: Prepare cache directories
  run: |
    mkdir -p /tmp/.buildx-cache
    mkdir -p /tmp/.buildx-cache-new
- name: Cache Docker layers
  uses: actions/cache@v4
  with:
    path: /tmp/.buildx-cache
    key: ${{ runner.os }}-buildx-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-buildx-
- name: Build Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    file: ./docker/Dockerfile
    push: false
    load: true
    tags: testopus:latest
    cache-from: type=local,src=/tmp/.buildx-cache
    cache-to: type=local,dest=/tmp/.buildx-cache-new,mode=max
- name: Move cache
  run: |
    rm -rf /tmp/.buildx-cache
    mv /tmp/.buildx-cache-new /tmp/.buildx-cache
```

These steps:
- Set up Docker Buildx for efficient builds
- Configure Docker layer caching to speed up builds
- Build the Docker image using the project's Dockerfile
- Optimize the cache for future builds

### 4. Test Execution

```yaml
- name: Run tests
  run: |
    if [ "${{ github.event.inputs.test_suite }}" = "ui" ]; then
      docker compose -f docker/docker-compose.yml run --rm testopus --verbose -vv --alluredir=/app/reports/allure-results --html=/app/reports/html/report.html --junitxml=/app/reports/junit/report_ui.xml /app/tests/ui_tests/web ${{ github.event.inputs.custom_flags }}
    elif [ "${{ github.event.inputs.test_suite }}" = "api" ]; then
      docker compose -f docker/docker-compose.yml run --rm testopus --verbose -vv --alluredir=/app/reports/allure-results --html=/app/reports/html/report.html --junitxml=/app/reports/junit/report_api.xml /app/tests/api_tests ${{ github.event.inputs.custom_flags }}
    elif [ "${{ github.event.inputs.test_suite }}" = "internal" ]; then
      docker compose -f docker/docker-compose.yml run --rm testopus --verbose -vv --alluredir=/app/reports/allure-results --html=/app/reports/html/report.html --junitxml=/app/reports/junit/report_internal.xml /app/tests/internal_tests ${{ github.event.inputs.custom_flags }}
    else
      docker compose -f docker/docker-compose.yml run --rm testopus --verbose -vv --alluredir=/app/reports/allure-results --html=/app/reports/html/report.html --junitxml=/app/reports/junit/report_all.xml /app/tests ${{ github.event.inputs.custom_flags }}
    fi
  env:
    DEBUG_MODE: ${{ github.event.inputs.debug_mode == 'true' }}
    PYTHONPATH: /app
    DOCKER_ENV: true
    PYTEST_ADDOPTS: --verbose
    TZ: Europe/Berlin
```

This step:
- Runs the tests in Docker using docker-compose
- Selects the appropriate test suite based on input
- Configures test output formats (Allure, HTML, JUnit)
- Sets environment variables for testing
- Uses Europe/Berlin timezone for consistent date formats

### 5. Report Generation

```yaml
- name: Set up Allure
  if: always()
  run: |
    wget -O allure-commandline.zip https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline/2.24.0/allure-commandline-2.24.0.zip
    unzip allure-commandline.zip
- name: Generate Allure Report
  if: always()
  run: |
    if [ -d "reports/allure-results" ] && [ "$(ls -A reports/allure-results)" ]; then
      # Set timezone to Berlin
      export TZ=Europe/Berlin
      
      # Generate the report
      ./allure-2.24.0/bin/allure generate reports/allure-results -o reports/allure-report --clean
      
      # Check if report generation was successful
      if [ $? -ne 0 ]; then
        echo "::warning::Allure report generation failed, creating dummy report"
        python3 ci/scripts/customize_allure_report.py --dummy
      else
        # Customize the report using our Python script
        python3 ci/scripts/customize_allure_report.py
      fi
    else
      echo "No Allure results found, creating a dummy report"
      python3 ci/scripts/customize_allure_report.py --dummy
    fi
  env:
    ALLURE_REPORT_DIR: reports/allure-report
    ALLURE_CREATE_DUMMY: false
    ALLURE_BRANCH: ${{ github.head_ref || github.ref_name }}
    GITHUB_REF: ${{ github.ref }}
    GITHUB_HEAD_REF: ${{ github.head_ref }}
```

These steps:
- Download and install Allure commandline tool
- Generate Allure report from test results
- Fall back to a dummy report if generation fails or no results exist
- Customize the report with our Python script
- Pass branch information for inclusion in the report

### 6. Artifact Upload

```yaml
- name: Upload test reports
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: test-reports
    path: |
      reports/html/
      reports/junit/
      reports/screenshots/
      reports/allure-results/
      reports/allure-report/
```

This step saves all test reports and results as workflow artifacts for later reference.

### 7. Test Results Publication

```yaml
- name: Publish Test Results
  if: always()
  uses: EnricoMi/publish-unit-test-result-action@v2
  with:
    files: reports/junit/report*.xml
    check_name: Test Results
```

This step:
- Publishes test results to GitHub's check interface
- Shows test status directly in the PR interface

### 8. GitHub Pages Deployment

```yaml
- name: Upload GitHub Pages artifact
  if: always()
  uses: actions/upload-pages-artifact@v3
  with:
    path: reports/allure-report
    retention-days: 30
- name: Deploy to reporting branch
  if: always()
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./reports/allure-report
    publish_branch: reporting
    force_orphan: true
    enable_jekyll: false
    keep_files: false
    cname: ${{ github.repository_owner }}.github.io/${{ github.event.repository.name }}
    user_name: "github-actions[bot]"
    user_email: "github-actions[bot]@users.noreply.github.com"
    commit_message: "docs: update Allure report [skip ci]"
```

These steps:
- Prepare the report for GitHub Pages
- Deploy the report to a dedicated 'reporting' branch
- Configure the deployment for optimal viewing

### 9. PR Comment

```yaml
- name: Comment PR with Report Links
  if: always() && github.event_name == 'pull_request'
  uses: actions/github-script@v7
  with:
    script: |
      const artifactUrl = `${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}`;
      let pagesUrl = `https://${{ github.repository_owner }}.github.io/${{ github.event.repository.name }}`;
      
      const comment = `### Test Results
      
      #### Report Links:
      - [Download Test Reports](${artifactUrl})
      - [View Allure Report](${pagesUrl}) (updated with latest results)
      
      *Tests run by GitHub Actions workflow*`;
      
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: comment
      });
```

This step adds a comment to PRs with links to test reports, making it easy for reviewers to access the results.

## Customizing the Workflow

### Adding a New Test Suite

To add a new test suite:

1. Add a new option to the `test_suite` input:
```yaml
options:
  - all
  - ui
  - api
  - internal
  - mynewsuite  # Add your new suite here
```

2. Add a new condition to the test execution step:
```yaml
elif [ "${{ github.event.inputs.test_suite }}" = "mynewsuite" ]; then
  docker compose -f docker/docker-compose.yml run --rm testopus --verbose -vv --alluredir=/app/reports/allure-results --html=/app/reports/html/report.html --junitxml=/app/reports/junit/report_mynewsuite.xml /app/tests/mynewsuite_tests ${{ github.event.inputs.custom_flags }}
```

### Changing the Deployment Target

To deploy reports to a different location:

1. Modify the GitHub Pages deployment step:
```yaml
- name: Deploy to reporting branch
  with:
    publish_branch: my-custom-branch  # Change this to your desired branch
```

### Adding Environment Variables

To add new environment variables to the test execution:

1. Modify the env section of the test execution step:
```yaml
env:
  DEBUG_MODE: ${{ github.event.inputs.debug_mode == 'true' }}
  PYTHONPATH: /app
  DOCKER_ENV: true
  PYTEST_ADDOPTS: --verbose
  TZ: Europe/Berlin
  MY_NEW_VAR: my-value  # Add your new environment variable here
```

## Troubleshooting

### Tests Not Running

If tests aren't running correctly:

1. Check the workflow run logs for errors
2. Verify Docker image builds successfully
3. Ensure test paths are correct in the workflow file
4. Check that required environment variables are set

### Report Generation Fails

If report generation fails:

1. Check the Allure results directory exists and contains files
2. Verify Allure commandline tool downloads successfully
3. Check for errors in the customize_allure_report.py script execution
4. Ensure file permissions are correct on the reports directory

### GitHub Pages Deployment Issues

If GitHub Pages deployment fails:

1. Verify GitHub Pages is enabled for the repository
2. Check the 'reporting' branch exists and is configured as a Pages source
3. Ensure the workflow has appropriate permissions
4. Check for errors in the GitHub Pages deployment logs 