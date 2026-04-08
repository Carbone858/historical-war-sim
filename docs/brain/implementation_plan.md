# Implementation Plan - Automated Session Management

This plan establishes a professional workflow for "Start" and "End" session operations, ensuring the local codebase is always synchronized with the remote GitHub repository.

## User Review Required

> [!IMPORTANT]
> **Git Authentication**
> I will use the established Git configuration. Please ensure your GitHub credentials (SSH key or Token) are cached locally so I can push without manual password entry.

> [!WARNING]
> **Auto-Commit Scope**
> The `end-session` workflow will stage **all** changes in the repository. Please ensure you have a proper `.gitignore` (which you do) to avoid committing environment files or sensitive data.

## Proposed Changes

### 1. Workflow Definitions
Create the `.agents/workflows` directory to host the session automation scripts.

#### [NEW] [session-start.md](file:///c:/Users/t3sfo/Desktop/historical-war-sim/historical-war-sim/.agents/workflows/session-start.md)
- Step 1: Fetch and pull latest changes from `origin main`.
- Step 2: Sync brain artifacts from `docs/brain/` back to the local environment if necessary.
- Step 3: Display a summary of the current task state.

#### [NEW] [session-end.md](file:///c:/Users/t3sfo/Desktop/historical-war-sim/historical-war-sim/.agents/workflows/session-end.md)
- Step 1: Copy all current artifacts (plans, walkthroughs, tasks) from the local brain to the repository's `docs/brain/` folder.
- Step 2: Stage all changed files and new brain artifacts.
- Step 3: Generate a descriptive commit message based on the recent conversation logs.
- Step 4: Push to `origin main`.

### 2. Automation Utilities
#### [NEW] [sync_progress.py](file:///c:/Users/t3sfo/Desktop/historical-war-sim/historical-war-sim/tools/sync_progress.py)
- A Python helper to handle the Git execution using the absolute path to `git.exe` (`C:\Program Files\Git\bin\git.exe`).

## Verification Plan

### Automated Tests
- Run `session-start` to verify connectivity (Pull).
- Run `session-end` with a dummy file to verify Stage -> Commit -> Push cycle.

### Manual Verification
- Verify the new commit appears on [GitHub](https://github.com/Carbone858/historical-war-sim).
