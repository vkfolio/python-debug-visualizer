# Publishing Notes - Python Debug Visualizer

This document covers how to publish both the VS Code extension and Python package.

---

## Part 1: VS Code Extension (Marketplace)

### Prerequisites

1. **Microsoft/Azure DevOps Account**
   - Go to https://dev.azure.com
   - Sign in with Microsoft account

2. **Create Publisher** (one-time)
   - Go to https://marketplace.visualstudio.com/manage
   - Click "Create publisher"
   - Choose unique publisher ID (e.g., `vigneshkarnika`)
   - Update `package.json`: `"publisher": "your-publisher-id"`

3. **Create Personal Access Token (PAT)**
   - Azure DevOps → Profile icon → Personal access tokens
   - Create new token:
     - **Organization**: All accessible organizations
     - **Scopes**: Click "Show all scopes" → Marketplace → **Manage**
   - Save token immediately (can't view again)

### Required Files

| File | Purpose |
|------|---------|
| `package.json` | Extension metadata, publisher, version |
| `README.md` | Marketplace listing page |
| `LICENSE` | License file (MIT recommended) |
| `CHANGELOG.md` | Version history (optional but recommended) |
| `icon.png` | 128x128 icon (optional but recommended) |
| `.vscodeignore` | Exclude files from package |

### package.json Required Fields

```json
{
  "name": "extension-name",
  "displayName": "Display Name (must be unique)",
  "description": "Short description",
  "version": "0.1.0",
  "publisher": "your-publisher-id",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/user/repo"
  },
  "engines": {
    "vscode": "^1.84.0"
  }
}
```

### .vscodeignore Example

```
.vscode/**
src/**
.gitignore
**/tsconfig.json
**/.eslintrc*
**/*.map
**/*.ts
!**/*.d.ts
*.vsix
**/test/**
```

### Publishing Commands

```bash
# Install vsce globally
npm install -g @vscode/vsce

# Navigate to extension folder
cd extension

# Login (paste PAT when prompted)
vsce login your-publisher-id

# Package locally (creates .vsix for testing)
vsce package

# Publish to marketplace
vsce publish

# Publish with version bump
vsce publish minor  # 0.1.0 → 0.2.0
vsce publish patch  # 0.1.0 → 0.1.1
```

### Troubleshooting

| Error | Solution |
|-------|----------|
| 401 Unauthorized | Create new PAT with correct permissions |
| Display name taken | Change `displayName` in package.json |
| Too many files | Add exclusions to `.vscodeignore` |
| Missing LICENSE | Create LICENSE file |

### Post-Publish

- Extension appears at: `https://marketplace.visualstudio.com/items?itemName=publisher.extension-name`
- Updates: bump version in `package.json`, run `vsce publish`

---

## Part 2: Python Package (PyPI)

### Prerequisites

1. **PyPI Account**
   - Register at https://pypi.org/account/register/
   - Verify email

2. **Create API Token**
   - Go to https://pypi.org/manage/account/token/
   - Create token (scope: "Entire account" for first upload)
   - Save token (starts with `pypi-`)

### Required Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Package metadata and build config |
| `README.md` | PyPI listing page |
| `LICENSE` | License file |
| `__init__.py` | Package initialization |

### pyproject.toml Example

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pydebugvisualizer"
version = "0.1.0"
description = "Package description"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"}
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
requires-python = ">=3.8"
dependencies = []

[project.urls]
Homepage = "https://github.com/user/repo"
Repository = "https://github.com/user/repo"

[tool.setuptools.packages.find]
where = ["."]
include = ["yourpackage*"]
```

### Publishing Commands

```bash
# Install build tools
pip install build twine

# Navigate to package folder
cd python-package

# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build package (creates dist/ folder)
python -m build

# Upload to PyPI
python -m twine upload dist/*
# Username: __token__
# Password: pypi-YOUR_TOKEN_HERE
```

### Save Credentials (Optional)

Create `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE
```

### Test on TestPyPI First (Optional)

```bash
# Upload to test server
python -m twine upload --repository testpypi dist/*

# Test install from test server
pip install -i https://test.pypi.org/simple/ pydebugvisualizer
```

### Troubleshooting

| Error | Solution |
|-------|----------|
| 403 Forbidden | Check token permissions, verify email |
| Name already exists | Choose different package name |
| Invalid metadata | Check pyproject.toml syntax |
| Missing README | Ensure README.md exists |

### Post-Publish

- Package appears at: `https://pypi.org/project/pydebugvisualizer/`
- Install: `pip install pydebugvisualizer`
- Updates: bump version in `pyproject.toml`, rebuild, upload

---

## Version Numbering (Semantic Versioning)

```
MAJOR.MINOR.PATCH (e.g., 1.2.3)

MAJOR: Breaking changes
MINOR: New features (backwards compatible)
PATCH: Bug fixes (backwards compatible)
```

- Start with `0.1.0` for initial release
- Use `0.x.x` while in development/alpha
- Move to `1.0.0` when stable

---

## Quick Reference

### VS Code Extension
```bash
cd extension
vsce login vigneshkarnika
vsce publish
```

### Python Package
```bash
cd python-package
rm -rf dist/ build/ *.egg-info
python -m build
python -m twine upload dist/*
```

---

## Links

- VS Code Marketplace: https://marketplace.visualstudio.com/manage
- Azure DevOps (PAT): https://dev.azure.com
- PyPI: https://pypi.org
- TestPyPI: https://test.pypi.org
- vsce docs: https://code.visualstudio.com/api/working-with-extensions/publishing-extension
- PyPI docs: https://packaging.python.org/tutorials/packaging-projects/
