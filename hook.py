import itertools
import random
import time
import requests

from colorama import Fore, Style, init


# ==========================================
# COLOR SETUP
# ==========================================

init(autoreset=True)


# ==========================================
# CONFIG
# ==========================================

WEBHOOK_URL = "https://discord.com/api/webhooks/1555755034007044097/XNE3_prOmIl-x3xaHkojJATGm_zcaVcE4mtON0OSt_uDkiCGKo9gCWIV4zamGhewFlGF"

CHARACTERS = "abcdefghijklmnopqrstuvwxyz0123456789"

MIN_LENGTH = 2
MAX_LENGTH = 3

# Delay between checks.
MIN_DELAY = 2.0
MAX_DELAY = 3.5

# Stop once an available username is found.
STOP_AFTER_FIRST_VALID = True

CHECK_URL = (
    "https://discord.com/api/v9/"
    "unique-username/username-attempt-unauthed"
)


# ==========================================
# SESSION
# ==========================================

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Accept": "application/json",
})


# ==========================================
# ASCII
# ==========================================

def print_banner():

    print(
        Fore.MAGENTA
        + r"""
██╗      █████╗ ██████╗ ██████╗
██║     ██╔══██╗██╔══██╗██╔══██╗
██║     ███████║██████╔╝██████╔╝
██║     ██╔══██║██╔══██╗██╔═══╝
███████╗██║  ██║██║  ██║██║
╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝
"""
    )

    print(
        Fore.CYAN
        + "        @piratefpss"
    )

    print(
        Fore.MAGENTA
        + "=" * 40
    )


# ==========================================
# WEBHOOK
# ==========================================

def send_webhook(username):

    payload = {
        "username": "LARP",
        "embeds": [
            {
                "title": "Username Found",
                "description": (
                    f"[+] `{username}` valid"
                ),
                # Discord green embed
                "color": 0x00FF00,
                "fields": [
                    {
                        "name": "Username",
                        "value": f"`{username}`",
                        "inline": True,
                    },
                    {
                        "name": "Status",
                        "value": "Available",
                        "inline": True,
                    },
                ],
                "footer": {
                    "text": "LARP Username Finder"
                },
            }
        ],
    }

    try:

        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            timeout=10,
        )

        if response.status_code in (
            200,
            204,
        ):

            print(
                Fore.CYAN
                + f"[WEBHOOK] Sent {username}"
            )

            return True

        print(
            Fore.YELLOW
            + "[WEBHOOK ERROR] "
            + f"{response.status_code} "
            + response.text
        )

        return False

    except requests.RequestException as error:

        print(
            Fore.YELLOW
            + f"[WEBHOOK ERROR] {error}"
        )

        return False


# ==========================================
# SAVE AVAILABLE USERNAME
# ==========================================

def save_username(username):

    with open(
        "available.txt",
        "a",
        encoding="utf-8",
    ) as file:

        file.write(
            username + "\n"
        )


# ==========================================
# CHECK USERNAME
# ==========================================

def check_username(username):

    try:

        response = session.post(
            CHECK_URL,
            json={
                "username": username
            },
            timeout=15,
        )

        # ==============================
        # RATE LIMIT
        # ==============================

        if response.status_code == 429:

            try:

                data = response.json()

                retry_after = float(
                    data.get(
                        "retry_after",
                        10,
                    )
                )

            except Exception:

                retry_after = 10

            print(
                Fore.YELLOW
                + "[RATE LIMITED] "
                + f"Waiting {retry_after:.1f}s"
            )

            time.sleep(
                retry_after + 1
            )

            return None

        # ==============================
        # BAD RESPONSE
        # ==============================

        if response.status_code != 200:

            print(
                Fore.YELLOW
                + f"[ERROR] {username} "
                + f"HTTP {response.status_code}"
            )

            return None

        # ==============================
        # RESPONSE
        # ==============================

        data = response.json()

        taken = data.get(
            "taken"
        )

        # ==============================
        # AVAILABLE
        # ==============================

        if taken is False:

            print(
                Fore.GREEN
                + Style.BRIGHT
                + f"[+] {username} VALID"
            )

            save_username(
                username
            )

            send_webhook(
                username
            )

            return True

        # ==============================
        # TAKEN
        # ==============================

        elif taken is True:

            print(
                Fore.RED
                + f"[-] {username} taken"
            )

            return False

        # ==============================
        # UNKNOWN
        # ==============================

        else:

            print(
                Fore.YELLOW
                + f"[?] {username} "
                + f"unknown response: {data}"
            )

            return None

    except requests.RequestException as error:

        print(
            Fore.YELLOW
            + f"[ERROR] {username}: {error}"
        )

        return None


# ==========================================
# GENERATOR
# ==========================================

def generate_usernames():

    usernames = []

    for length in range(
        MIN_LENGTH,
        MAX_LENGTH + 1,
    ):

        combinations = itertools.product(
            CHARACTERS,
            repeat=length,
        )

        for combination in combinations:

            username = "".join(
                combination
            )

            usernames.append(
                username
            )

    # Random order
    random.shuffle(
        usernames
    )

    return usernames


# ==========================================
# MAIN
# ==========================================

def main():

    print_banner()

    print()

    print(
        Fore.WHITE
        + f"Length     : "
        + Fore.CYAN
        + f"{MIN_LENGTH}-{MAX_LENGTH}"
    )

    print(
        Fore.WHITE
        + "Characters : "
        + Fore.CYAN
        + CHARACTERS
    )

    print(
        Fore.WHITE
        + "Mode       : "
        + Fore.GREEN
        + "Search until valid"
    )

    print()

    print(
        Fore.MAGENTA
        + "=" * 40
    )

    print()

    usernames = generate_usernames()

    total = len(
        usernames
    )

    checked = 0
    found = 0

    print(
        Fore.CYAN
        + f"Generated {total:,} usernames."
    )

    print(
        Fore.CYAN
        + "Starting checker..."
    )

    print()

    try:

        for username in usernames:

            result = check_username(
                username
            )

            checked += 1

            # ==========================
            # VALID FOUND
            # ==========================

            if result is True:

                found += 1

                print()

                print(
                    Fore.GREEN
                    + Style.BRIGHT
                    + "=" * 40
                )

                print(
                    Fore.GREEN
                    + Style.BRIGHT
                    + "VALID USERNAME FOUND!"
                )

                print(
                    Fore.GREEN
                    + Style.BRIGHT
                    + f"Username: {username}"
                )

                print(
                    Fore.GREEN
                    + Style.BRIGHT
                    + f"Checked : {checked:,}"
                )

                print(
                    Fore.GREEN
                    + Style.BRIGHT
                    + "=" * 40
                )

                if STOP_AFTER_FIRST_VALID:

                    break

            # ==========================
            # STATUS
            # ==========================

            print(
                Fore.WHITE
                + "Checked: "
                + Fore.CYAN
                + f"{checked:,}/{total:,}"
                + Fore.WHITE
                + " | Found: "
                + Fore.GREEN
                + str(found)
            )

            # ==========================
            # DELAY
            # ==========================

            delay = random.uniform(
                MIN_DELAY,
                MAX_DELAY,
            )

            time.sleep(
                delay
            )

    except KeyboardInterrupt:

        print()

        print(
            Fore.YELLOW
            + "[!] Checker stopped by user."
        )

    finally:

        print()

        print(
            Fore.MAGENTA
            + "=" * 40
        )

        print(
            Fore.WHITE
            + "Checked: "
            + Fore.CYAN
            + f"{checked:,}"
        )

        print(
            Fore.WHITE
            + "Valid:   "
            + Fore.GREEN
            + f"{found}"
        )

        print(
            Fore.MAGENTA
            + "=" * 40
        )


# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    main()