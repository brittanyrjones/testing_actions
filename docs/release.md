# Release Pull Request Process

This document describes how the "Create Release Pull Request" workflow operates and how to use it.

---

## Overview

The **Create Release Pull Request** workflow is designed to automate the process of preparing

## Manual Release Workflow

You can trigger a release using the **Manual Release** workflow in GitHub Actions.

### Steps

1. Go to the **Actions** tab in your GitHub repository.
2. Select the **Manual Release** workflow.
3. Click **Run workflow**.
4. Enter the tag name you want to release (e.g., `v0.3.20beta` or `v0.3.20`).
5. Click **Run workflow**.

### What Happens

- The workflow checks out the code at the specified tag.
- It sets up Python and installs dependencies.
- It builds the package into the `dist/` directory.
- If the tag name contains `beta`:
  - The package is published to [TestPyPI](https://test.pypi.org/project/bjones-testing-actions).
  - A draft GitHub release is created.
- If the tag name does **not** contain `beta`:
  - The package is published to [PyPI](https://pypi.org/project/bjones-testing-actions).
  - A draft GitHub release is created.

### Notes

- **Trusted Publishing** is used for PyPI/TestPyPI uploads. The project must already exist on PyPI/TestPyPI for the workflow to succeed.
- If you see a 400 error about "Non-user identities cannot create new projects," manually upload the first release to PyPI/TestPyPI.

### Useful Links

- [TestPyPI Project](https://test.pypi.org/project/bjones-testing-actions)
- [PyPI Project](https://pypi.org/project/bjones-testing-actions)
