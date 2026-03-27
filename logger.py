import datetime
import os

LOG_FILE = "logs.txt"


#  Write log entry
def write_log(message):

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = f"[{timestamp}] {message}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(entry)


#  Read all logs for dashboard
def read_logs():

    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r", encoding="utf-8") as file:
        lines = file.readlines()

    return lines[::-1]
