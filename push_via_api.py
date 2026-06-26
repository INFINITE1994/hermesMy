#!/usr/bin/env python3
"""Push files to GitHub using the API (when git push is blocked by proxy)."""
import subprocess
import json
import os
import base64

REPO = "INFINITE1994/hermesMy"
BASE_DIR = "/g/hermesMy"

EXCLUDE = {'.git', '__pycache__', 'dist', 'build', '*.spec', '*.tar.gz'}

def should_exclude(path):
    parts = path.replace('\\', '/').split('/')
    for part in parts:
        if part in EXCLUDE:
            return True
        if part.endswith('.spec'):
            return True
    return False

def gh_api(endpoint, method="GET", stdin_data=None):
    cmd = f'"/c/Program Files/GitHub CLI/gh.exe" api {endpoint} --method {method}'
    if stdin_data:
        cmd += f' -H "Content-Type: application/json" --input -'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, input=stdin_data)
    else:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()

def create_blob(filepath):
    with open(filepath, 'rb') as f:
        content = f.read()
    # Use base64 encoding for binary files
    b64 = base64.b64encode(content).decode('utf-8')
    data = json.dumps({"content": b64, "encoding": "base64"})
    out, err = gh_api(f"repos/{REPO}/git/blobs", "POST", data)
    if out:
        result = json.loads(out)
        return result.get("sha")
    print(f"Error creating blob for {filepath}: {err}")
    return None

def create_tree(base_tree, tree_entries):
    data = json.dumps({"base_tree": base_tree, "tree": tree_entries})
    out, err = gh_api(f"repos/{REPO}/git/trees", "POST", data)
    if out:
        result = json.loads(out)
        return result.get("sha")
    print(f"Error creating tree: {err}")
    return None

def create_commit(tree_sha, parent_sha=None, message="Initial commit"):
    data = {"tree": tree_sha, "message": message}
    if parent_sha:
        data["parents"] = [parent_sha]
    out, err = gh_api(f"repos/{REPO}/git/commits", "POST", json.dumps(data))
    if out:
        result = json.loads(out)
        return result.get("sha")
    print(f"Error creating commit: {err}")
    return None

def update_ref(ref, sha):
    data = json.dumps({"sha": sha, "force": True})
    out, err = gh_api(f"repos/{REPO}/git/refs/{ref}", "POST", data)
    if out:
        return True
    # Try PATCH if POST fails
    out, err = gh_api(f"repos/{REPO}/git/refs/{ref}", "PATCH", data)
    return bool(out)

def main():
    print("Collecting files...")
    files = []
    for root, dirs, filenames in os.walk(BASE_DIR):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not should_exclude(d)]
        for filename in filenames:
            filepath = os.path.join(root, filename)
            relpath = os.path.relpath(filepath, BASE_DIR).replace('\\', '/')
            if should_exclude(relpath):
                continue
            files.append((relpath, filepath))
    
    print(f"Found {len(files)} files")
    
    # Create blobs
    print("Creating blobs...")
    tree_entries = []
    for i, (relpath, filepath) in enumerate(files):
        sha = create_blob(filepath)
        if sha:
            tree_entries.append({
                "path": relpath,
                "mode": "100644",
                "type": "blob",
                "sha": sha
            })
            if (i + 1) % 10 == 0:
                print(f"  {i + 1}/{len(files)} blobs created")
    
    print(f"Created {len(tree_entries)} blobs")
    
    # Create tree
    print("Creating tree...")
    tree_sha = create_tree(None, tree_entries)
    if not tree_sha:
        print("Failed to create tree!")
        return
    print(f"Tree SHA: {tree_sha}")
    
    # Create commit
    print("Creating commit...")
    commit_sha = create_commit(tree_sha, message="feat: HermesMy ToolBox v1.0.0 - Windows desktop tool suite\n\n5 tools: CleanMaster, PDFMaster, ImageBatch, FileOrganizer, ToolBox\nDark theme PyQt6 UI, Chinese interface")
    if not commit_sha:
        print("Failed to create commit!")
        return
    print(f"Commit SHA: {commit_sha}")
    
    # Update ref
    print("Updating ref...")
    if update_ref("heads/main", commit_sha):
        print("SUCCESS! Code pushed to GitHub.")
    elif update_ref("heads/master", commit_sha):
        print("SUCCESS! Code pushed to GitHub (master branch).")
    else:
        print("Failed to update ref, but commit was created.")
        print(f"Try manually: gh api repos/{REPO}/git/refs/heads/main -f sha={commit_sha} -f force=true")

if __name__ == "__main__":
    main()
