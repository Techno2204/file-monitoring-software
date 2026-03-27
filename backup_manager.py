import os
import shutil

BACKUP_DIR = "backup_files"


def ensure_backup_folder():
    os.makedirs(BACKUP_DIR, exist_ok=True)


def safe_backup_name(path):
    return path.replace(":", "").replace("\\", "__").replace("/", "__")


def unsafe_restore_name(name):
    restored = name.replace("__", "\\")

    if len(restored) > 1 and restored[1] == "\\":
        restored = restored[0] + ":\\" + restored[2:]

    return restored


#  Backup Modified Files
def create_backup(file_paths):
    ensure_backup_folder()

    for file_path in file_paths:

        if not os.path.exists(file_path):
            continue

        backup_path = os.path.join(BACKUP_DIR, safe_backup_name(file_path))

        if os.path.exists(backup_path):
            continue

        try:
            shutil.copy2(file_path, backup_path)
        except:
            continue


#  Restore File
def restore_file(file_path):
    ensure_backup_folder()

    backup_path = os.path.join(BACKUP_DIR, safe_backup_name(file_path))

    if not os.path.exists(backup_path):
        return False

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        shutil.copy2(backup_path, file_path)
        return True
    except:
        return False


#  Update Backup After Approval
def update_backup(file_path):
    ensure_backup_folder()

    if not os.path.exists(file_path):
        return False

    backup_path = os.path.join(BACKUP_DIR, safe_backup_name(file_path))

    try:
        shutil.copy2(file_path, backup_path)
        return True
    except:
        return False


#  Backup Folder Before Delete (ONLY if contains files)
def backup_folder(folder_path):
    ensure_backup_folder()

    if not os.path.exists(folder_path):
        return False

    backed_up = False

    for root, _, files in os.walk(folder_path):
        for file in files:

            full_path = os.path.join(root, file)

            backup_path = os.path.join(
                BACKUP_DIR,
                safe_backup_name(full_path)
            )

            if os.path.exists(backup_path):
                continue

            try:
                shutil.copy2(full_path, backup_path)
                backed_up = True
            except:
                continue

    return backed_up


#  Restore Folder (only restores backed-up files)
def restore_folder(folder_path):
    ensure_backup_folder()

    restored = False

    for backup_file in os.listdir(BACKUP_DIR):

        original_path = unsafe_restore_name(backup_file)

        if original_path.lower().startswith(folder_path.lower()):

            backup_full = os.path.join(BACKUP_DIR, backup_file)

            try:
                os.makedirs(os.path.dirname(original_path), exist_ok=True)
                shutil.copy2(backup_full, original_path)
                restored = True
            except:
                continue

    return restored


#  Rename Backup Paths When Folder Rename Approved
def rename_backup_folder(old_folder, new_folder):
    ensure_backup_folder()

    for backup_file in os.listdir(BACKUP_DIR):

        original_path = unsafe_restore_name(backup_file)

        if original_path.lower().startswith(old_folder.lower()):

            renamed_original = original_path.replace(old_folder, new_folder, 1)

            old_backup_path = os.path.join(BACKUP_DIR, backup_file)

            new_backup_name = safe_backup_name(renamed_original)
            new_backup_path = os.path.join(BACKUP_DIR, new_backup_name)

            try:
                if os.path.exists(new_backup_path):
                    os.remove(new_backup_path)

                os.rename(old_backup_path, new_backup_path)

            except:
                continue
