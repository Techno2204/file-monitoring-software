from flask import Flask, render_template, request, redirect
import os
import json
import threading
import time
import shutil
from urllib.parse import unquote

from monitor import scan_folder, detect_changes, detect_folder_changes
from logger import write_log, read_logs
from report_generator import generate_report

from baseline_manager import (
    create_baseline,
    load_baseline,
    approve_file_change,
    approve_added_file,
    approve_added_folder,
    approve_file_rename,
    approve_folder_rename
)

from backup_manager import (
    restore_file,
    restore_folder,
    create_backup,
    update_backup,
    rename_backup_folder,
    backup_folder
)

app = Flask(__name__)

CONFIG_FILE = "config.json"
monitoring_status = False

scan_results = {
    "added": [],
    "deleted": [],
    "modified": [],
    "renamed": [],
    "added_folders": [],
    "deleted_folders": [],
    "renamed_folders": []
}
#  Prevent Duplicate Report Spam (Smart Rule 1)
last_report_signature = None

#  Reset Scan Results
def reset_scan():
    global scan_results
    scan_results = {
        "added": [],
        "deleted": [],
        "modified": [],
        "renamed": [],
        "added_folders": [],
        "deleted_folders": [],
        "renamed_folders": []
    }


#  Load Folder Path
def load_folder():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f).get("folder", "")
    return ""


#  Save Folder Path
def save_folder(path):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"folder": path}, f)


#  Risk Score
def risk_score(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in [".exe", ".dll", ".sys"]:
        return "HIGH "
    elif ext in [".txt", ".pdf", ".docx"]:
        return "MEDIUM "
    return "LOW "


# ==========================================================
#  HOME
# ==========================================================
@app.route("/")
def home():
    folder = load_folder()

    if folder and os.path.exists(folder):
        files, folders = scan_folder(folder)
        files_count = len(files)
        folders_count = max(0, len(folders) - 1)
        threat = "SAFE " if not scan_results["modified"] else "ALERT "
    else:
        folder = "Not Configured"
        files_count = 0
        folders_count = 0
        threat = "NOT READY "

    return render_template(
        "home.html",
        folder=folder,
        files_count=files_count,
        folders_count=folders_count,
        threat=threat,
        monitoring=monitoring_status
    )


# ==========================================================
#  SETTINGS
# ==========================================================
@app.route("/settings", methods=["GET", "POST"])
def settings():
    folder = load_folder()

    if request.method == "POST":
        new_folder = request.form["folder"]

        if os.path.exists(new_folder):
            save_folder(new_folder)
            reset_scan()
            write_log(f" Monitoring Folder Updated: {new_folder}")
        else:
            write_log(" Invalid Folder Entered!")

        return redirect("/")

    return render_template("settings.html", folder=folder)


# ==========================================================
#  BASELINE
# ==========================================================
@app.route("/baseline", methods=["GET", "POST"])
def baseline():
    folder = load_folder()

    if request.method == "POST":
        create_baseline(folder)
        reset_scan()
        write_log(" Baseline Created Successfully!")
        return redirect("/scan_live")

    return render_template("baseline.html", folder=folder)


# ==========================================================
#  LIVE SCAN PAGE
# ==========================================================
@app.route("/scan_live")
def scan_live():
    return render_template(
        "scan.html",
        monitoring=monitoring_status,
        added=scan_results["added"],
        deleted=scan_results["deleted"],
        modified=scan_results["modified"],
        renamed=scan_results["renamed"],
        added_folders=scan_results["added_folders"],
        deleted_folders=scan_results["deleted_folders"],
        renamed_folders=scan_results["renamed_folders"]
    )


# ==========================================================
#  START / STOP MONITORING
# ==========================================================
@app.route("/start_monitoring")
def start_monitoring():
    global monitoring_status
    monitoring_status = True

    threading.Thread(target=monitoring_loop, daemon=True).start()
    write_log(" Live Monitoring Started")

    return redirect("/")


@app.route("/stop_monitoring")
def stop_monitoring():
    global monitoring_status
    monitoring_status = False
    write_log(" Live Monitoring Stopped")
    return redirect("/")


# ==========================================================
#  BACKGROUND LOOP
# ==========================================================
def monitoring_loop():
    global scan_results, last_report_signature

    folder = load_folder()

    while monitoring_status:

        if not os.path.exists("baseline.json"):
            time.sleep(3)
            continue

        old_files, old_folders = load_baseline()
        new_files, new_folders = scan_folder(folder)

        added_folders, deleted_folders, renamed_folders = detect_folder_changes(
            old_folders, new_folders, folder
        )

        modified, deleted, added, renamed = detect_changes(
            old_files, new_files, renamed_folders
        )

        #  Backup modified files
        create_backup(modified)

        #  Store results for UI
        scan_results["added"] = [(f, risk_score(f)) for f in added]
        scan_results["deleted"] = [(f, risk_score(f)) for f in deleted]

        scan_results["modified"] = [
            (f, risk_score(f), new_files[f]["hash"]) for f in modified
        ]

        scan_results["renamed"] = renamed
        scan_results["added_folders"] = added_folders
        scan_results["deleted_folders"] = deleted_folders
        scan_results["renamed_folders"] = renamed_folders

        #  SMART REPORT SIGNATURE
        if added or deleted or modified or renamed or added_folders or deleted_folders:

            current_signature = (
                tuple(sorted(added)),
                tuple(sorted(deleted)),
                tuple(sorted(modified)),
                tuple(sorted(renamed)),
                tuple(sorted(added_folders)),
                tuple(sorted(deleted_folders)),
                tuple(sorted(renamed_folders))
            )

            #  Generate report only if change is NEW
            if current_signature != last_report_signature:

                generate_report(
                    modified, deleted, added, renamed,
                    added_folders, deleted_folders, renamed_folders
                )

                write_log(" New Integrity Report Generated!")
                last_report_signature = current_signature

        time.sleep(3)



#  Approve Modified File
@app.route("/approve_file")
def approve_file():
    path = unquote(request.args.get("path"))

    files, _ = scan_folder(load_folder())

    approve_file_change(
        path,
        files[path]["hash"],
        os.path.getsize(path),
        os.path.getmtime(path)
    )

    #  Update backup to new trusted version
    update_backup(path)

    #  Baseline rebuild immediately
    create_baseline(load_folder())

    reset_scan()
    return redirect("/scan_live")


#  Reject Modified File (Restore old backup)
@app.route("/reject_file")
def reject_file():
    path = unquote(request.args.get("path"))

    restore_file(path)

    #  Baseline rebuild after restore
    create_baseline(load_folder())

    reset_scan()
    return redirect("/scan_live")


#  Approve Added File
@app.route("/approve_added")
def approve_added():
    path = unquote(request.args.get("path"))

    approve_added_file(path)

    #  Backup approved file immediately
    update_backup(path)

    #  Baseline rebuild
    create_baseline(load_folder())

    reset_scan()
    return redirect("/scan_live")


#  Approve Added Folder
@app.route("/approve_added_folder")
def approve_added_folder_route():
    path = unquote(request.args.get("path"))

    approve_added_folder(path)

    #  Baseline rebuild immediately
    create_baseline(load_folder())

    write_log(f" Folder Approved: {path}")

    reset_scan()
    return redirect("/scan_live")


#  Delete Added File
@app.route("/delete_added")
def delete_added():
    path = unquote(request.args.get("path"))

    if os.path.exists(path):
        os.remove(path)

    reset_scan()
    return redirect("/scan_live")


#  Restore Deleted File
@app.route("/restore_file")
def restore_deleted_file():
    path = unquote(request.args.get("path"))

    restore_file(path)
    create_baseline(load_folder())

    reset_scan()
    return redirect("/scan_live")


#  Delete Folder
@app.route("/delete_folder")
def delete_folder():
    path = unquote(request.args.get("path"))

    backup_folder(path)

    if os.path.exists(path):
        shutil.rmtree(path)

    write_log(f"🗑 Folder Deleted & Backup Saved: {path}")

    reset_scan()
    return redirect("/scan_live")


#  Restore Folder
@app.route("/restore_folder")
def restore_deleted_folder():
    path = unquote(request.args.get("path"))

    restored = restore_folder(path)

    if restored:
        write_log(f" Folder Restored Successfully: {path}")
        create_baseline(load_folder())
    else:
        write_log(f" Folder Restore Failed: {path}")

    reset_scan()
    return redirect("/scan_live")


#  Approve Rename File
@app.route("/approve_rename")
def approve_rename():
    old = unquote(request.args.get("old"))
    new = unquote(request.args.get("new"))

    approve_file_rename(old, new)

    #  Baseline rebuild
    create_baseline(load_folder())

    write_log(f" Rename Approved: {old} → {new}")

    reset_scan()
    return redirect("/scan_live")


#  Approve Rename Folder
@app.route("/approve_folder_rename")
def approve_folder_rename_route():
    old = unquote(request.args.get("old"))
    new = unquote(request.args.get("new"))

    approve_folder_rename(old, new)
    rename_backup_folder(old, new)

    #  Baseline rebuild
    create_baseline(load_folder())

    write_log(f" Folder Rename Approved: {old} → {new}")

    reset_scan()
    return redirect("/scan_live")

#  Reject File Rename
@app.route("/reject_rename")
def reject_rename():
    old = unquote(request.args.get("old"))
    new = unquote(request.args.get("new"))

    #  Restore rename back
    if os.path.exists(new):
        os.rename(new, old)

    #  Update baseline immediately
    create_baseline(load_folder())

    reset_scan()
    write_log(f" File Rename Rejected: Restored {new} → {old}")

    return redirect("/scan_live")

#  Reject Folder Rename
@app.route("/reject_folder_rename")
def reject_folder_rename():
    old = unquote(request.args.get("old"))
    new = unquote(request.args.get("new"))

    #  Restore folder name back
    if os.path.exists(new):
        os.rename(new, old)

    #  Also rename backup folder mapping back
    rename_backup_folder(new, old)

    #  Update baseline immediately
    create_baseline(load_folder())

    reset_scan()
    write_log(f" Folder Rename Rejected: Restored {new} → {old}")

    return redirect("/scan_live")

#  Logs
@app.route("/logs")
def logs():
    return render_template("logs.html", logs=read_logs())


#  Reports
@app.route("/reports")
def reports():
    if not os.path.exists("reports"):
        os.mkdir("reports")

    reports_list = sorted(os.listdir("reports"), reverse=True)
    return render_template("reports.html", reports=reports_list)

from flask import send_from_directory

#  Download Report File Route
@app.route("/download_report/<filename>")
def download_report(filename):

    reports_dir = os.path.join(os.getcwd(), "reports")

    #  Security: Only allow files inside reports folder
    return send_from_directory(
        directory=reports_dir,
        path=filename,
        as_attachment=True
    )


#  Run App
if __name__ == "__main__":
    app.run(debug=True)
