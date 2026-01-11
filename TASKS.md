# TASKS.md — PyAurora4X Project Improvements

> Authoritative task ledger + memory anchor for implementing systematic improvements to PyAurora4X without merge conflicts.
Rule: Only pick next batch from unchecked tasks [ ]. Add new work here first (ANTI-DRIFT).

---

## 0) Run Protocol (mandatory every run)

- [x] Read TASKS.md fully and pick next batch ONLY from unchecked tasks.
- [x] Confirm this run's batch + exit criteria are explicitly listed under "1) Current Batch".
- [x] End of run: update TASKS.md + STATUS.md + IMPROVEMENTS_INVENTORY.md, produce artifact, output link + changelog + next plan.

---

## 1) Current Batch (choose ONE batch at a time)

> Fill in the batch you are executing BEFORE doing work.

### Batch ID: BATCH-001

**Batch Type:**

- [x] Initial Setup & Documentation
- [ ] Code Implementation
- [ ] Testing & Validation
- [ ] Cleanup & Maintenance

**Exit Criteria for this batch:**

- [x] TASKS.md created with complete task breakdown
- [x] STATUS.md created with initial state
- [x] IMPROVEMENTS_INVENTORY.md created with all improvement items from open PRs
- [x] CHANGELOG.md created for tracking progress
- [x] All tracking files reviewed and validated
- [x] TASKS.md updated truthfully with links to outputs
- [x] STATUS.md updated with results
- [x] Initial documentation package produced and linked

---

## 2) Coverage Strategy

- [x] Define scope: Work on open pull requests without introducing merge conflicts
- [x] Enumerate improvement items from open PRs:
  - PR #47: Add workflow to capture UI screenshot
  - PR #21: Remove attached_assets (already resolved - directory doesn't exist)
- [x] Create IMPROVEMENTS_INVENTORY.md with status tracking
- [x] Document items excluded from processing and rationale - [IMPROVEMENTS_INVENTORY.md](IMPROVEMENTS_INVENTORY.md#exclusions)
- [x] Add "Coverage Strategy" section to STATUS.md - [STATUS.md](STATUS.md#coverage-strategy)

---

## 3) Deliverables (top-down order)

### Core Tracking Files

- [x] Create TASKS.md (this file) - [/home/runner/work/PyAurora4X/PyAurora4X/TASKS.md](TASKS.md)
- [x] Create STATUS.md with current state - [/home/runner/work/PyAurora4X/PyAurora4X/STATUS.md](STATUS.md)
- [x] Create IMPROVEMENTS_INVENTORY.md with status tags - [/home/runner/work/PyAurora4X/PyAurora4X/IMPROVEMENTS_INVENTORY.md](IMPROVEMENTS_INVENTORY.md)
- [x] Create CHANGELOG.md documenting milestones - [/home/runner/work/PyAurora4X/PyAurora4X/CHANGELOG.md](CHANGELOG.md)

### PR #47: UI Screenshot Workflow

- [ ] Analyze PR #47 requirements
  - [ ] Understand screenshot capture mechanism
  - [ ] Review workflow requirements
  - [ ] Check for conflicts with existing code
- [ ] Create screenshot capture script
  - [ ] Script to capture UI in SVG format
  - [ ] Script documentation
  - [ ] Test script functionality
- [ ] Create GitHub Actions workflow
  - [ ] Define workflow triggers
  - [ ] Configure screenshot artifact publishing
  - [ ] Test workflow configuration
- [ ] Update documentation
  - [ ] Update README.md to reference screenshot artifact
  - [ ] Document workflow usage

### PR #21: Remove attached_assets

- [x] Verify attached_assets directory status (confirmed: doesn't exist)
- [x] Document resolution in IMPROVEMENTS_INVENTORY.md
- [x] Mark as [COMPLETED] in inventory

### Documentation Improvements

- [ ] Review existing documentation for completeness
- [ ] Identify gaps in project documentation
- [ ] Create or update documentation as needed
- [ ] Ensure all tracking files are up to date

### Quality/Testing

- [ ] Run existing test suite to establish baseline
- [ ] Test screenshot capture script
- [ ] Validate GitHub Actions workflow
- [ ] Run full test suite to ensure no regressions

---

## 4) Quality Gates (repeat regularly)

### Code Quality Audit

- [ ] All Python code follows existing style conventions
- [ ] No new linting errors introduced
- [ ] All scripts have proper error handling
- [ ] All new code has appropriate documentation

### Testing Audit

- [ ] Existing test suite passes
- [ ] New functionality tested appropriately
- [ ] No test regressions introduced
- [ ] Test coverage maintained or improved

### Documentation Audit

- [ ] All tracking files (TASKS.md, STATUS.md, IMPROVEMENTS_INVENTORY.md, CHANGELOG.md) are current
- [ ] README.md updated with new features
- [ ] All changes properly documented
- [ ] Links in documentation are valid

---

## 5) Cleanup & Maintenance

- [ ] Remove temporary files created during development
  - [ ] Check /tmp directory
  - [ ] Remove test artifacts
- [ ] Verify .gitignore covers generated files
- [ ] Clean up any debug code or comments
- [ ] Ensure no sensitive data in commits

---

## 6) Version Control & Release

- [ ] Review all staged changes for commit
  - [ ] Tracking documentation files
  - [ ] Screenshot capture script
  - [ ] GitHub Actions workflow
  - [ ] README updates
- [ ] Create detailed commit message documenting:
  - [ ] Systematic task tracking implementation
  - [ ] UI screenshot workflow addition
  - [ ] Documentation improvements
- [ ] Push staged changes to remote
- [ ] Verify PR description is up to date

---

## 7) Future Improvements

- [ ] Investigate additional workflow automations
- [ ] Consider adding more screenshot formats (PNG, JPEG)
- [ ] Explore automated documentation generation
- [ ] Review other potential repository improvements
- [ ] Consider adding pre-commit hooks for documentation
- [ ] Evaluate CI/CD improvements

---

## 8) Packaging & Delivery (every run)

- [ ] Update STATUS.md with batch completion status
- [ ] Update IMPROVEMENTS_INVENTORY.md tags ([TODO]/[IN_PROGRESS]/[COMPLETED])
- [ ] Produce documentation package:
  - [ ] All tracking files in repository root
  - [ ] Scripts in appropriate locations
  - [ ] Workflows in .github/workflows/
- [ ] Output: artifact link + changelog + next execution plan

---

## 9) Known Blockers & Dependencies

- [ ] No major blockers identified
- [ ] GitHub Actions requires proper permissions for artifact upload
- [ ] Screenshot script depends on Textual being properly installed
- [ ] Workflow testing requires pushing to repository

---

## 10) Next Immediate Actions (Priority Order)

- [x] Create TASKS.md (this file)
- [ ] Create STATUS.md with initial project state
- [ ] Create IMPROVEMENTS_INVENTORY.md with all improvement items
- [ ] Create CHANGELOG.md for progress tracking
- [ ] Begin implementation of PR #47 improvements
- [ ] Test and validate all changes
- [ ] Update all tracking documentation
- [ ] Complete batch and report progress

---

## Usage Notes

This file serves as the authoritative source of truth for all work on this PR. Before doing any work not listed here, add it to this file first (ANTI-DRIFT RULE). Mark items [x] only when truly completed and verified.

### Key Principles

- **ANTI-DRIFT**: Add tasks to TASKS.md BEFORE doing work not already listed
- **Batch execution**: Pick ONE batch at a time, define exit criteria upfront
- **Truth in tracking**: Mark tasks complete only when verified
- **Durable artifacts**: Always produce STATUS.md, CHANGELOG.md, and deliverables
- **Interruption-safe**: Can pause/resume at any batch boundary
