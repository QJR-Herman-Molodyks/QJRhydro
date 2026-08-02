import os
import sys

def get_user_fs():
    # stable path (works in executable formats)
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) \
        else os.path.dirname(os.path.abspath(__file__))

    root = os.path.join(base_dir, "user")

    # list with needed directories
    folders = ["backup", "documents", "images", "logs", "music", "video"]

    # create root if there's not
    os.makedirs(root, exist_ok=True)

    # create needed directories (won't touch existing ones)
    for f in folders:
        os.makedirs(os.path.join(root, f), exist_ok=True)

    return root