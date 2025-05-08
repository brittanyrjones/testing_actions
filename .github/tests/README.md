# GitHub Actions Workflow Tests

This directory contains tests for validating GitHub Actions workflows. These tests are separate from the main project tests as they are only relevant for CI/CD development.

## Prerequisites

- Docker Desktop must be installed and running
- `act` must be installed (`brew install act`)

## Running the Tests

To run the workflow tests:

```bash
# From the .github/tests directory
pytest test_workflows.py -v

# Or from the project root
pytest .github/tests/test_workflows.py -v
```

## What's Being Tested

The tests validate:
1. Workflow syntax and structure
2. Presence of required steps
3. Correct trigger conditions
4. Required permissions

Tests run in `--dry-run` mode, which means they validate the workflow structure without executing the actual actions.

## When to Run These Tests

Run these tests when:
- Making changes to workflow files
- Before merging changes to workflow files
- Debugging workflow issues

These tests are not part of the main project test suite and are not included in normal test runs or coverage reports. 
