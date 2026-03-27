import json
import os
from monitor import scan_folder

BASELINE_FILE = "baseline.json"


def save_baseline(data):
    with open(BASELINE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def load_baseline():
    if not os.path.exists(BASELINE_FILE):
        return {}, set()

    try:
        with open(BASELINE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("files", {}), set(data.get("folders", []))
    except:
        return {}, set()


def create_baseline(folder_path):
    files_data, folder_data = scan_folder(folder_path)

    baseline = {
        "files": files_data,
        "folders": list(folder_data)
    }

    save_baseline(baseline)


def approve_file_change(file_path, new_hash, new_size, new_time):
    files, folders = load_baseline()

    files[file_path] = {
        "hash": new_hash,
        "size": new_size,
        "modified_time": new_time
    }

    save_baseline({"files": files, "folders": list(folders)})


def approve_added_file(file_path):
    files, folders = load_baseline()

    if os.path.exists(file_path):
        files[file_path] = {
            "hash": "trusted",
            "size": os.path.getsize(file_path),
            "modified_time": os.path.getmtime(file_path)
        }

    save_baseline({"files": files, "folders": list(folders)})


def approve_added_folder(folder_path):
    files, folders = load_baseline()

    if os.path.exists(folder_path):
        folders.add(folder_path)

    save_baseline({"files": files, "folders": list(folders)})


def approve_file_rename(old_path, new_path):
    files, folders = load_baseline()

    if old_path in files:
        files[new_path] = files.pop(old_path)

    save_baseline({"files": files, "folders": list(folders)})


def approve_folder_rename(old_folder, new_folder):
    files, folders = load_baseline()

    updated_files = {}

    for path, meta in files.items():
        if path.startswith(old_folder):
            updated_files[path.replace(old_folder, new_folder, 1)] = meta
        else:
            updated_files[path] = meta

    updated_folders = set()
    for f in folders:
        if f.startswith(old_folder):
            updated_folders.add(f.replace(old_folder, new_folder, 1))
        else:
            updated_folders.add(f)

    save_baseline({"files": updated_files, "folders": list(updated_folders)})
