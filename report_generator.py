import os
from datetime import datetime


#  Risk Scoring Function
def calculate_risk(path):
    high = [".exe", ".dll", ".sys", "config", "system"]
    medium = [".doc", ".pdf", ".txt", ".log"]

    p = path.lower()

    for k in high:
        if k in p:
            return "HIGH "

    for k in medium:
        if k in p:
            return "MEDIUM "

    return "LOW "


# =====================================================
#  SOC STYLE INTEGRITY INCIDENT REPORT GENERATOR
# =====================================================
def generate_report(modified, deleted, added,
                    renamed,
                    added_folders, deleted_folders, renamed_folders):

    #  Ensure Reports Directory Exists
    if not os.path.exists("reports"):
        os.mkdir("reports")

    #  Timestamp Report File
    time_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_name = f"reports/report_{time_now}.txt"

    with open(report_name, "w", encoding="utf-8") as file:

        #  HEADER
        file.write("====================================================\n")
        file.write("        🛡 FILE INTEGRITY INCIDENT REPORT\n")
        file.write("====================================================\n\n")

        file.write(f"📅 Date & Time Detected : {datetime.now()}\n\n")

        #  SUMMARY COUNTS
        file.write("=============== SUMMARY ===============\n")
        file.write(f" Added Files        : {len(added)}\n")
        file.write(f" Deleted Files      : {len(deleted)}\n")
        file.write(f" Modified Files     : {len(modified)}\n")
        file.write(f" Renamed Files      : {len(renamed)}\n\n")

        file.write(f"📁 Added Folders      : {len(added_folders)}\n")
        file.write(f"🗑 Deleted Folders    : {len(deleted_folders)}\n")
        file.write(f"🔄 Renamed Folders    : {len(renamed_folders)}\n")
        file.write("=======================================\n\n")

        #  MODIFIED FILES SECTION
        if modified:
            file.write("\n⚠ MODIFIED FILES DETECTED\n")
            file.write("---------------------------------------\n")

            for m in modified:
                risk = calculate_risk(m)
                file.write(f"✏ File Changed : {m}\n")
                file.write(f"   Risk Level  : {risk}\n")
                file.write("   Meaning     : File content was altered.\n")
                file.write("   Threat      : Possible malware injection or tampering.\n\n")

        #  DELETED FILES SECTION
        if deleted:
            file.write("\n❌ DELETED FILES DETECTED\n")
            file.write("---------------------------------------\n")

            for d in deleted:
                risk = calculate_risk(d)
                file.write(f"🗑 File Deleted : {d}\n")
                file.write(f"   Risk Level   : {risk}\n")
                file.write("   Meaning      : File was removed from system.\n")
                file.write("   Threat       : Could indicate attacker cleanup or ransomware.\n\n")

        #  ADDED FILES SECTION
        if added:
            file.write("\n NEW FILES ADDED\n")
            file.write("---------------------------------------\n")

            for a in added:
                risk = calculate_risk(a)
                file.write(f" New File Created : {a}\n")
                file.write(f"   Risk Level       : {risk}\n")
                file.write("   Meaning          : File was added unexpectedly.\n")
                file.write("   Threat           : Could be unauthorized dropper or payload.\n\n")

        #  RENAMED FILES SECTION
        if renamed:
            file.write("\n FILE RENAMES DETECTED\n")
            file.write("---------------------------------------\n")

            for old, new in renamed:
                file.write(f"✏ Renamed File : {old}  →  {new}\n")
                file.write("   Meaning     : File identity was changed.\n")
                file.write("   Threat      : Attackers may rename to hide malicious tools.\n\n")

        #  FOLDER CHANGES
        if added_folders:
            file.write("\n NEW FOLDERS CREATED\n")
            file.write("---------------------------------------\n")

            for f in added_folders:
                file.write(f" Folder Added : {f}\n")
                file.write("   Meaning      : New directory appeared.\n")
                file.write("   Threat       : Could be staging area for malware.\n\n")

        if deleted_folders:
            file.write("\n FOLDERS DELETED\n")
            file.write("---------------------------------------\n")

            for f in deleted_folders:
                file.write(f" Folder Deleted : {f}\n")
                file.write("   Meaning        : Entire directory removed.\n")
                file.write("   Threat         : Could indicate destructive attack.\n\n")

        if renamed_folders:
            file.write("\n FOLDER RENAMES DETECTED\n")
            file.write("---------------------------------------\n")

            for old, new in renamed_folders:
                file.write(f" Folder Renamed : {old} → {new}\n")
                file.write("   Meaning        : Directory name was changed.\n")
                file.write("   Threat         : Attackers rename folders to confuse monitoring.\n\n")

        #  FINAL RECOMMENDATIONS
        file.write("\n====================================================\n")
        file.write(" SOC RECOMMENDED ACTIONS\n")
        file.write("====================================================\n")

        file.write("1. Review all HIGH risk modifications immediately.\n")
        file.write("2. Restore deleted files if unauthorized.\n")
        file.write("3. Verify added files/folders are expected.\n")
        file.write("4. If suspicious → Run antivirus + forensic scan.\n")
        file.write("5. Check Audit Logs for responsible user/process.\n")

        file.write("\n END OF INCIDENT REPORT\n")

    return report_name
