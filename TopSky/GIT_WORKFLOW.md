# Git Workflow for TopSkyMaps

## Quick Start

```bash
# Navigate to your local repo
cd /path/to/your/repo

# Copy the output files
cp /path/to/downloads/TopSkyMaps.txt .
cp /path/to/downloads/README.md .

# Stage and commit
git add TopSkyMaps.txt README.md
git commit -m "v1.0.0: Initial TopSkyMaps build with CHARLO-NO-CONTROL"

# Push to remote
git push origin main
```

## Version Update Workflow

When updating the file after each build session:

```bash
# 1. Update version in TopSkyMaps.txt header
#    Change: VERSION: 1.0.0 → 1.1.0 (minor) or 1.0.1 (patch)
#    Update: BUILD DATE and CHANGELOG

# 2. Copy updated file
cp /path/to/downloads/TopSkyMaps.txt .

# 3. Stage, commit with semantic message
git add TopSkyMaps.txt
git commit -m "v1.1.0: Add northern Labrador Class G boundary"

# 4. Create git tag (optional but recommended)
git tag -a v1.1.0 -m "Added northern Labrador Class G"

# 5. Push with tags
git push origin main --tags
```

## Semantic Versioning Guide

**Format:** MAJOR.MINOR.PATCH (e.g., 1.2.3)

- **MAJOR** (1.x.x): Breaking changes, complete restructure
  - Example: "2.0.0: Complete rewrite with new layer strategy"
  
- **MINOR** (x.1.x): New boundaries added, new features
  - Example: "1.1.0: Add CZUL neighbor boundaries (Layer 1)"
  - Example: "1.2.0: Add all TWR circles (Layer 2)"
  
- **PATCH** (x.x.1): Bug fixes, coordinate corrections, small tweaks
  - Example: "1.1.1: Fix CYHZ_TWR radius (7nm not 10nm)"
  - Example: "1.1.2: Adjust CHARLO color for better contrast"

## Commit Message Conventions

```bash
# Feature additions
git commit -m "feat: Add CYYR 87 NM MTCA boundary"
git commit -m "feat: Implement CZUL hot/cold state layers"

# Bug fixes
git commit -m "fix: Correct LFVP_TWR radius to 5 NM"
git commit -m "fix: Close CHARLO polygon properly"

# Documentation
git commit -m "docs: Update README with Layer 2 status"
git commit -m "docs: Add COORD_AF syntax examples"

# Refactoring
git commit -m "refactor: Convert TWR polygons to COORD_CIRCLE"
git commit -m "refactor: Simplify CYYR MTCA using arc geometry"

# Version releases
git commit -m "v1.1.0: Add Layer 1 cold neighbor boundaries"
```

## Branch Strategy (Optional)

For collaborative development:

```bash
# Create feature branch
git checkout -b feature/layer-2-twr-boundaries

# Make changes, commit
git add TopSkyMaps.txt
git commit -m "feat: Add all TWR circle boundaries"

# Push feature branch
git push origin feature/layer-2-twr-boundaries

# Merge to main (via PR or locally)
git checkout main
git merge feature/layer-2-twr-boundaries
git push origin main
```

## Viewing History

```bash
# See all commits
git log --oneline

# See changes in a specific commit
git show v1.1.0

# Compare versions
git diff v1.0.0 v1.1.0

# View file at specific version
git show v1.0.0:TopSkyMaps.txt
```

## Rollback If Needed

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Revert to specific version
git checkout v1.0.0 TopSkyMaps.txt
git commit -m "revert: Roll back to v1.0.0"
```

## .gitignore Recommendations

Create a `.gitignore` file:

```
# Working documents (not for git)
TOPSKYMAPS_TODO.md
TOPSKYMAPS_PROGRESS.md

# Backup files
*.bak
*~

# OS files
.DS_Store
Thumbs.db
```

## Best Practices

1. **Always update version number** in file header before committing
2. **Update changelog** in header with each version
3. **Use semantic versioning** consistently
4. **Write clear commit messages** that explain the "why"
5. **Tag releases** for easy rollback and reference
6. **Test before committing** - load in EuroScope to verify
7. **Keep commits atomic** - one logical change per commit

## Current Status Tracking

The TODO and PROGRESS markdown files stay **local only** (in Claude's working directory). Only `TopSkyMaps.txt` and `README.md` go to git. This keeps the repo clean while maintaining detailed development notes locally.

## Questions?

- TODO/PROGRESS not in git? **Correct** - they're working docs, not production
- When to create tags? **On every minor version** (1.1.0, 1.2.0, etc.)
- Can I edit directly in GitHub? **Not recommended** - maintain version control through local workflow
