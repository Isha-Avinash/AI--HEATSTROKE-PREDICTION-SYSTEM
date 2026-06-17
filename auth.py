import csv
import os

USER_FILE = "users.csv"

def register_user(username, password):

    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "password"])

    with open(USER_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([username, password])

def login_user(username, password):

    if not os.path.exists(USER_FILE):
        return False

    with open(USER_FILE, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row["username"] == username and row["password"] == password:
                return True

    return False