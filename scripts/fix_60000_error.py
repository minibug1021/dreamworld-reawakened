"""Fixes Nintendo WFC error 60000 when connecting to the Game Sync server.

This asks for the Friend Code on your Pal Pad, works the WFC profile id out
from it, and writes that id to every WFC profile in the game-sync database.
Restart the Game Sync server afterwards.

    python scripts/fix_60000_error.py
"""
import hashlib
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))  # run as a script, so make the project importable

from game_sync_server.entralinked.utility.db_manager import db  # noqa: E402

FRIEND_CODE_DIGITS = 12
PID_MASK = 0x7FFFFFFF       # the profile id is the Friend Code's low 31 bits
GAME_CODE_SUFFIX = b"JARI"  # hashed together with the profile id for the checksum


def calculate_pid(friend_code: str) -> int:
    """Return the WFC profile id in a Friend Code.

    Raise ValueError if the code is malformed or its checksum is wrong.
    """
    friend_code = friend_code.replace("-", "").replace(" ", "")

    if len(friend_code) != FRIEND_CODE_DIGITS:
        raise ValueError(f"Friend Code must contain {FRIEND_CODE_DIGITS} digits.")

    if not friend_code.isdigit():
        raise ValueError("Friend Code must contain only digits.")

    code = int(friend_code)
    low_32_bits = (code & 0xFFFFFFFF).to_bytes(4, "little")
    checksum = code >> 32
    expected_checksum = hashlib.md5(low_32_bits + GAME_CODE_SUFFIX).digest()[0] >> 1

    if checksum != expected_checksum:
        raise ValueError("Friend Code is invalid. Please double-check your Pal Pad.")

    return code & PID_MASK


def main() -> None:
    """Asks for a Friend Code and gives every stored WFC profile its profile id."""
    print("Error 60000 Fix\n")

    friend_code = input("Enter your in-game Friend Code from your Pal Pad (with or without dashes): ")

    pid = calculate_pid(friend_code)

    print(f"\nCalculated PID: {pid}")

    users = db.get_all_wfc_users()

    if not users:
        print("No WFC profiles found in the database.")
        return

    print(f"Found {len(users)} WFC user(s).\n")

    for user in users:
        profiles = user["profiles"]
        if not profiles:
            continue

        for profile_name, profile in profiles.items():
            print(f"{user['id']}: {profile_name} ({profile.get('id')} -> {pid})")
            profile["id"] = pid

        db.save_wfc_user(user_id=user["id"], password=user["password"], profiles=profiles)

    print("\nDone.")
    print("Restart the game sync server and try connecting again.")


if __name__ == "__main__":
    main()
