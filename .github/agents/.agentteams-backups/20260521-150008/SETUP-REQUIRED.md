# SETUP-REQUIRED.md

The following **3 placeholder(s)** remain unresolved for project **ResearchTeam** and require manual attention.

---

## 1. `{STYLE_REFERENCE_PATH}`

**Found in:** `multiple`
**Context:** A formal external style guide path is not configured.

**Action required:** Keep the current value (`N/A — no formal style guide defined for this project`) or replace it with a project style guide path if one is created.

---

## 2. `{PIP_PACKAGE_NAME}`

**Found in:** `multiple`
**Context:** Repository packaging metadata is not configured as a Python package.

**Action required:** Keep `N/A` unless this repository is made installable; if packaging is added, update affected agent files.

---

## 3. `{DOC_SITE_CONFIG_FILE}`

**Found in:** `multiple`
**Context:** Static documentation site config is not configured.

**Action required:** Keep `N/A` unless docs-site generation is added; if added, set the config path in affected agent files.

---

Once all items above are resolved, invoke `@conflict-auditor` to verify consistency.
