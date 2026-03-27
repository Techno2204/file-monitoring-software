import os
from hash_utils import get_file_hash

IGNORE_FOLDERS = [
    ".venv", ".idea", "__pycache__",
    "backup_files", "reports"
]


#  Scan Folder
def scan_folder(folder_path):

    file_data = {}
    folder_data = set()

    for root, dirs, files in os.walk(folder_path):

        dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]

        folder_data.add(root)

        for file in files:
            full_path = os.path.join(root, file)

            try:
                file_data[full_path] = {
                    "hash": get_file_hash(full_path),
                    "mtime": os.path.getmtime(full_path)
                }
            except:
                continue

    return file_data, folder_data


#  Detect Folder Changes
def detect_folder_changes(old_folders, new_folders, root_folder):

    added = list(new_folders - old_folders)
    deleted = list(old_folders - new_folders)

    added = [f for f in added if f != root_folder]
    deleted = [f for f in deleted if f != root_folder]

    renamed = []

    for old in deleted[:]:
        for new in added[:]:
            if os.path.dirname(old) == os.path.dirname(new):
                renamed.append((old, new))
                deleted.remove(old)
                added.remove(new)

    return added, deleted, renamed


#  Detect File Changes (FINAL FIXED)
def detect_changes(old_files, new_files, renamed_folders):

    modified, deleted, added, renamed = [], [], [], []

    #  Deleted + Modified
    for old_path in old_files:

        if old_path not in new_files:

            if any(old_path.startswith(r[0]) for r in renamed_folders):
                continue

            deleted.append(old_path)

        else:
            if old_files[old_path]["hash"] != new_files[old_path]["hash"]:
                modified.append(old_path)

    #     #  Added Files
    for new_path in new_files:

        if new_path not in old_files:

            if any(new_path.startswith(r[1]) for r in renamed_folders):
                continue

            added.append(new_path)

    #  Rename Detection ONLY in SAME folder
    for d in deleted[:]:
        old_hash = old_files[d]["hash"]
        old_parent = os.path.dirname(d)

        for a in added[:]:
            new_parent = os.path.dirname(a)

            #  Only rename if same folder
            if new_parent == old_parent:
                if new_files[a]["hash"] == old_hash:
                    renamed.append((d, a))
                    deleted.remove(d)
                    added.remove(a)
                    break

    return modified, deleted, added, renamed
