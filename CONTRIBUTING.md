# Contributing to CZQM/CZQX vACC Resources

Thank you for your interest in contributing! These resources serve CZQM/CZQX vACC controllers and the broader VATSIM community.

---

## 🎯 Ways to Contribute

### 1. Report Bugs & Issues
Found something broken? Let us know!

**[Open an Issue →](https://github.com/skyelaird/CZQM-vACC/issues/new)**

**When reporting, please include:**
- Product and version (e.g., "TopSky Complete v0.9.0")
- EuroScope version
- Operating system
- Steps to reproduce
- Expected vs. actual behavior
- Screenshots or error messages (if applicable)

### 2. Suggest Features
Have an idea for improvement?

**[Open a Feature Request →](https://github.com/skyelaird/CZQM-vACC/issues/new)**

**Good feature requests include:**
- Clear description of the feature
- Use case / problem it solves
- Example of how it would work
- Any alternatives you've considered

### 3. Submit Pull Requests
Code contributions welcome!

**Before submitting:**
1. Fork the repository
2. Create a feature branch (`feature/your-feature-name`)
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### 4. Share Your Configurations
Created a great ASR profile or custom TopSky setup?

**Share it:**
- Open an issue with your configuration attached
- Include screenshots showing it in action
- Describe what makes it unique/useful

### 5. Improve Documentation
Found something unclear?

**Help improve docs:**
- Fix typos or unclear explanations
- Add examples or screenshots
- Translate documentation (if applicable)
- Write tutorials or guides

---

## 📋 Contribution Guidelines

### Code Style

#### Python
```python
# Use descriptive variable names
# Follow PEP 8 style guide
# Include docstrings for functions

def generate_rf_arc(center_lat, center_lon, radius_nm, start_bearing, end_bearing):
    """
    Generate RF arc coordinates for TopSky display.
    
    Args:
        center_lat (float): Center latitude in decimal degrees
        center_lon (float): Center longitude in decimal degrees
        radius_nm (float): Arc radius in nautical miles
        start_bearing (float): Starting bearing in degrees
        end_bearing (float): Ending bearing in degrees
    
    Returns:
        list: List of coordinate tuples [(lat1, lon1), (lat2, lon2), ...]
    """
    # Implementation...
```

#### JavaScript
```javascript
// Use modern ES6+ syntax
// Clear variable names
// Comment complex logic

function calculateRunwayRecommendation(wind, runways) {
    // Calculate crosswind component for each runway
    const recommendations = runways.map(runway => {
        const crosswind = calculateCrosswind(wind, runway.heading);
        return { ...runway, crosswind };
    });
    
    // Sort by lowest crosswind
    return recommendations.sort((a, b) => a.crosswind - b.crosswind);
}
```

### Documentation Style

#### Markdown Files
- Use clear, concise language
- Include code examples where applicable
- Use proper heading hierarchy (h1 → h2 → h3)
- Include table of contents for long documents

#### Comments in Configuration Files
```
; TopSky configuration file
; Section: Display Settings
;
; Display refresh rate in milliseconds
; Valid range: 100-1000
; Recommended: 500 (default)
REFRESH_RATE:500
```

### Commit Messages

Use clear, descriptive commit messages:

```
Good:
✅ "feat: Add CYQM ground radar profile"
✅ "fix: Correct RF arc radius for CYHZ runway 05"
✅ "docs: Update MAESTRO training guide"

Bad:
❌ "update"
❌ "fix stuff"
❌ "changes"
```

**Format:**
```
type: Brief description (50 chars or less)

More detailed explanation if needed (wrap at 72 characters).
Include the motivation for the change and contrast with previous behavior.

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

---

## 🧪 Testing Guidelines

### Before Submitting
- [ ] Test in EuroScope (if applicable)
- [ ] Verify all links work
- [ ] Check for typos and grammar
- [ ] Ensure files use correct encoding (UTF-8)
- [ ] Test on different screen resolutions (for ASR files)

### For TopSky Configurations
- [ ] Test with multiple aircraft
- [ ] Verify coordination works correctly
- [ ] Check display at different zoom levels
- [ ] Ensure no performance issues

### For Web Applications
- [ ] Test in Chrome, Firefox, Safari
- [ ] Test on mobile devices
- [ ] Verify offline functionality
- [ ] Check responsive design

---

## 📂 File Organization

### Adding New Files

**TopSky ASR Profiles:**
```
TopSky/source/TS_Beta/ASR/
├── [POSITION]/              # e.g., YHZ, CTR
│   └── [POSITION]_[TYPE].asr
```

**Ground Radar Profiles:**
```
GroundRadar/
├── [AIRPORT]/
│   ├── [AIRPORT]-GND_GRP.asr
│   └── [AIRPORT]-TWR-GRP.asr
```

**Documentation:**
```
docs/
├── [category]/              # e.g., training, procedures
│   └── [document].md
```

### File Naming Conventions
- Use UPPERCASE for ICAO codes (CYHZ, CYQM)
- Use hyphens for multi-word names (`training-guide.md`)
- Include version in filename if applicable (`v1.0.0`)

---

## 🔍 Code Review Process

### What We Look For
1. **Functionality** — Does it work as intended?
2. **Code Quality** — Is it well-written and maintainable?
3. **Documentation** — Are changes documented?
4. **Testing** — Has it been tested thoroughly?
5. **Compatibility** — Works with existing systems?

### Review Timeline
- Small changes: 1-3 days
- Medium changes: 3-7 days
- Large changes: 1-2 weeks

### Feedback
- All feedback is constructive
- Requested changes help maintain quality
- Questions welcome during review

---

## 🤝 Community Guidelines

### Be Respectful
- Treat all contributors with respect
- Focus on ideas, not individuals
- Assume good intentions
- No harassment or discrimination

### Be Constructive
- Provide helpful, actionable feedback
- Explain *why* when suggesting changes
- Offer alternatives when criticizing

### Be Patient
- Maintainers are volunteers
- Reviews take time
- Not all suggestions can be implemented

---

## 🏷️ Issue Labels

We use labels to organize issues:

- `bug` — Something isn't working
- `enhancement` — New feature request
- `documentation` — Improvements to docs
- `question` — Need clarification
- `good first issue` — Good for newcomers
- `help wanted` — Extra attention needed
- `wontfix` — Won't be addressed
- `duplicate` — Already reported

---

## 📝 License

By contributing, you agree that your contributions will be licensed under the same license as the project (GPL-3.0).

See [LICENSE](LICENSE) for details.

---

## 🙋 Questions?

**Not sure where to start?**
- Look for [`good first issue`](https://github.com/skyelaird/CZQM-vACC/labels/good%20first%20issue) labels
- Ask questions in issues
- Contact maintainers via CZQM/CZQX Discord

**Need help with Git/GitHub?**
- [GitHub Docs](https://docs.github.com)
- [Git Tutorial](https://git-scm.com/docs/gittutorial)
- Ask in the issues — we're happy to help!

---

## 🎉 Recognition

Contributors will be:
- Listed in release notes
- Credited in CHANGELOG.md
- Thanked in README.md acknowledgments

Significant contributions may earn:
- GitHub contributor badge
- Special mention in announcements
- Our eternal gratitude! 🙏

---

## 📧 Contact

**Maintainer:** Joel Laird (VE1ATM)  
**VATSIM:** VATCAN Division  
**vACC:** CZQM/CZQX

**Preferred contact methods:**
1. [GitHub Issues](https://github.com/skyelaird/CZQM-vACC/issues)
2. CZQM/CZQX Discord
3. VATCAN forums

---

*Thank you for contributing to CZQM/CZQX vACC resources!*
