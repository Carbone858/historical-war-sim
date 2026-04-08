import os
import subprocess
import shutil
import sys

# Configuration
GIT_PATH = r"C:\Program Files\Git\bin\git.exe"
REPO_ROOT = r"c:\Users\t3sfo\Desktop\historical-war-sim\historical-war-sim"
# Dynamically find the brain directory from the environment if possible, or use the known one
BRAIN_DIR = r"C:\Users\t3sfo\.gemini\antigravity\brain\bc7ed368-68fd-4d8e-a50e-1fc5833fe4e6"
DOCS_BRAIN_DIR = os.path.join(REPO_ROOT, "docs", "brain")

def run_git(args, cwd=REPO_ROOT):
    cmd = [GIT_PATH] + args
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(result.stdout)
    return True

def sync_brain_to_repo():
    print("Syncing Brain Artifacts to Repository...")
    if not os.path.exists(DOCS_BRAIN_DIR):
        os.makedirs(DOCS_BRAIN_DIR)
    
    # Copy all .md artifacts
    for item in os.listdir(BRAIN_DIR):
        if item.endswith(".md"):
            src = os.path.join(BRAIN_DIR, item)
            dst = os.path.join(DOCS_BRAIN_DIR, item)
            shutil.copy2(src, dst)
            print(f"Copied {item} to docs/brain/")

def sync_repo_to_brain():
    print("Syncing Repository Brain Assets to Local Brain...")
    if not os.path.exists(DOCS_BRAIN_DIR):
        return
    
    for item in os.listdir(DOCS_BRAIN_DIR):
        if item.endswith(".md"):
            src = os.path.join(DOCS_BRAIN_DIR, item)
            dst = os.path.join(BRAIN_DIR, item)
            shutil.copy2(src, dst)
            print(f"Restored {item} to local brain.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python sync_progress.py [start|end] [commit_message]")
        return

    action = sys.argv[1].lower()
    
    if action == "start":
        print("--- Starting Session Sync ---")
        if run_git(["pull", "origin", "main"]):
            sync_repo_to_brain()
            print("Session Start Sync Complete.")
    
    elif action == "end":
        commit_msg = sys.argv[2] if len(sys.argv) > 2 else "End of Session: Progress Update"
        print(f"--- Ending Session Sync: {commit_msg} ---")
        
        sync_brain_to_repo()
        
        if run_git(["add", "."]):
            if run_git(["commit", "-m", commit_msg]):
                if run_git(["push", "origin", "main"]):
                    print("Session End Sync Complete. Brain and Code synchronized to GitHub.")
                else:
                    print("Push failed.")
            else:
                print("Commit failed (might be no changes).")
        else:
            print("Add failed.")

if __name__ == "__main__":
    main()
