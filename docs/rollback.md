# Rollback Process

This document describes how to roll back a release.

## PyPI and TestPyPI Policy

- **PyPI and TestPyPI do not allow deleting or overwriting existing releases with the same version number.**
- Once a version is published, it cannot be replaced. You must publish a new version.

## Rollback Steps

1. **Revert the code** in your repository to the desired previous state (e.g., using `git revert` or by checking out an earlier commit and creating a new branch).
2. **Bump the version** in your `pyproject.toml` to a new, unique version (e.g., `0.3.21` or `0.3.21beta`).
3. **Create a new tag** for the rollback version:
   ```sh
   git tag v0.3.21
   git push origin v0.3.21
   ```
4. **Trigger the Manual Release workflow** in GitHub Actions, specifying the new tag.

## Notes

- The previous (bad) release will still be available on PyPI/TestPyPI, but the new release will be the latest and recommended version.
- You may want to update your project documentation or release notes to indicate that a rollback has occurred.

## References

- [PyPI FAQ: Removing a release](https://pypi.org/help/#removing-a-release)
- [TestPyPI](https://test.pypi.org/project/bjones-testing-actions)
