# GitHub Actions Workflows for CZQM-vACC

## 📋 Overview

Two automated workflows to streamline version management and release publishing:

1. **version-bump.yml** - Automatically updates version numbers across all files
2. **create-release.yml** - Builds and publishes GitHub releases

## 🚀 Setup Instructions

### Step 1: Add Workflows to Repository

```bash
# From your CZQM-vACC repository root:
mkdir -p .github/workflows
cp create-release.yml .github/workflows/
cp version-bump.yml .github/workflows/
git add .github/workflows/
git commit -m "feat: add GitHub Actions workflows for automated releases"
git push
```

### Step 2: Verify Workflows

1. Go to https://github.com/skyelaird/CZQM-vACC/actions
2. You should see two workflows:
   - "Update Version Numbers"
   - "Create Release"

## 📝 Usage

### Workflow 1: Update Version Numbers

**When to use:** Before creating a new release

**Steps:**
1. Go to: https://github.com/skyelaird/CZQM-vACC/actions
2. Select "Update Version Numbers"
3. Click "Run workflow"
4. Fill in the form:
   - **TopSky Complete Version**: e.g., `0.9.02`
   - **TopSky Data Version**: e.g., `2025.12.01`
   - **Complete Changes**: Brief description (optional)
   - **Data Changes**: Brief description (optional)
5. Click "Run workflow"

**What it does:**
- ✅ Updates README.md (all version references)
- ✅ Updates Build-Releases.ps1 (all version references)
- ✅ Updates CHANGELOG.md (adds new entry)
- ✅ Commits changes automatically
- ✅ Pushes to GitHub

**Result:** All version numbers updated and committed to the repository!

---

### Workflow 2: Create Release

**When to use:** After updating version numbers

**Steps:**
1. Go to: https://github.com/skyelaird/CZQM-vACC/actions
2. Select "Create Release"
3. Click "Run workflow"
4. Fill in the form:
   - **Release Type**: Choose from:
     - `topsky-complete` - Only TopSky Complete
     - `topsky-data` - Only TopSky Data
     - `ground-radar` - Only Ground Radar Plugin
     - `all` - Create all three releases
   - **Version**: e.g., `0.9.01` or `2025.12.01`
   - **Description**: Release notes (optional)
5. Click "Run workflow"

**What it does:**
- ✅ Runs Build-Releases.ps1 on Windows runner
- ✅ Creates ZIP packages automatically
- ✅ Creates GitHub releases with proper tags
- ✅ Uploads ZIP files to releases
- ✅ Adds installation instructions
- ✅ Marks beta versions as pre-release

**Result:** GitHub releases published with download links!

## 🔄 Complete Release Process

### Typical Workflow

```
1. Make changes to TopSky files
   ↓
2. Run "Update Version Numbers" workflow
   ↓
3. Run "Create Release" workflow
   ↓
4. Done! Releases are live
```

### Example: Releasing v0.9.02

1. **Update versions:**
   - Run "Update Version Numbers"
   - Complete: `0.9.02`
   - Data: `2025.12.01`
   - Changes: "Fixed CZUL boundaries, added CYQM ground layout"

2. **Create releases:**
   - Run "Create Release"
   - Type: `all`
   - Version: `0.9.02` (for Complete) or `2025.12.01` (for Data)
   - Description: "See CHANGELOG.md for details"

3. **Result:**
   - Three releases created
   - All links in README.md work immediately
   - CHANGELOG.md is up to date

## 🔧 Manual Steps (If Needed)

### If Workflows Fail

1. **Check Actions tab** for error messages
2. **Common issues:**
   - Missing GITHUB_TOKEN permissions
   - Build-Releases.ps1 errors
   - File path issues

### Manual Release (Fallback)

If automated releases fail:

```bash
# 1. Build packages locally
powershell -File Build-Releases.ps1

# 2. Create release manually on GitHub
# Go to: https://github.com/skyelaird/CZQM-vACC/releases/new
# - Create tag (e.g., TopSky-Complete-v0.9.02)
# - Upload ZIP files from releases/ folder
# - Add release notes
```

## 📊 Workflow Files

### version-bump.yml

**Triggers:** Manual (workflow_dispatch)
**Runner:** Ubuntu-latest
**Language:** Python 3.11
**What it modifies:**
- README.md
- Build-Releases.ps1
- CHANGELOG.md

### create-release.yml

**Triggers:** Manual (workflow_dispatch)
**Runner:** Windows-latest
**What it uses:**
- PowerShell (for Build-Releases.ps1)
- softprops/action-gh-release (for releases)
- GITHUB_TOKEN (automatic)

## 🛠️ Customization

### Add New Release Type

Edit `create-release.yml`:

```yaml
options:
  - topsky-complete
  - topsky-data
  - ground-radar
  - maestro  # Add new type
  - all
```

Then add a new job step for the release.

### Change Version Format

Edit `version-bump.yml` Python script to match your versioning scheme.

### Modify Release Notes

Edit the `body:` sections in `create-release.yml`.

## 🔐 Permissions

Both workflows use `GITHUB_TOKEN` which is automatically provided by GitHub Actions. No additional secrets needed!

Required permissions:
- **contents: write** - To commit version changes and create releases
- **actions: write** - To run workflows

These are typically enabled by default.

## 📝 Notes

- **Beta versions** (v0.x.x) are automatically marked as pre-release
- **Data versions** follow AIRAC format (YYYY.MM.DD)
- **Complete versions** follow semantic versioning (Major.Minor.Patch)
- Workflows run on **GitHub's hosted runners** (free for public repos)

## 🆘 Troubleshooting

### "Workflow not found"
- Make sure files are in `.github/workflows/` directory
- Check file permissions (should be 644)
- Verify YAML syntax is valid

### "Build-Releases.ps1 failed"
- Check PowerShell syntax
- Verify file paths in script
- Ensure source files exist

### "Permission denied"
- Check repository settings → Actions → Workflow permissions
- Enable "Read and write permissions"

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [softprops/action-gh-release](https://github.com/softprops/action-gh-release)

---

**Created:** December 2, 2025  
**For:** CZQM/CZQX vACC - skyelaird/CZQM-vACC
