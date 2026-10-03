import itertools
import os
import random
import sys
import time

import requests
from colorama import Fore, Style, init


# ==========================================================
# LARP - Discord Short Username Finder
# ==========================================================

init(autoreset=True)


# ==========================================================
# CONFIG
# ==========================================================

WEBHOOK_URL = "https://discord.com/api/webhooks/1555755034007044097/XNE3_prOmIl-x3xaHkojJATGm_zcaVcE4mtON0OSt_uDkiCGKo9gCWIV4zamGhewFlGF"

CHECK_URL = (
    "https://discord.com/api/v9/"
    "unique-username/username-attempt-unauthed"
)

CHARACTERS = "abcdefghijklmnopqrstuvwxyz0123456789"

# Prioritize 3-character usernames first.
LENGTHS = [3, 2]

# Delay between normal checks.
MIN_DELAY = 3.0
MAX_DELAY = 5.0

# Stop after finding the first valid username.
STOP_AFTER_FIRST_VALID = True

CHECKED_FILE = "checked.txt"
AVAILABLE_FILE = "available.txt"

REQUEST_TIMEOUT = 20

# Extra cooldown added after Discord's retry_after.
RATE_LIMIT_BUFFER = 1.0


# ==========================================================
# SESSION
# ==========================================================

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Content-Type": "application/json",
})


# ==========================================================
# COLORS
# ==========================================================

GREEN = Fore.GREEN + Style.BRIGHT
RED = Fore.RED
YELLOW = Fore.YELLOW
CYAN = Fore.CYAN
MAGENTA = Fore.MAGENTA + Style.BRIGHT
WHITE = Fore.WHITE
DIM = Style.DIM


# ==========================================================
# BANNER
# ==========================================================

def banner():
    os.system("cls" if os.name == "nt" else "clear")

    print(
        MAGENTA
        + r"""
██╗      █████╗ ██████╗ ██████╗
██║     ██╔══██╗██╔══██╗██╔══██╗
██║     ███████║██████╔╝██████╔╝
██║     ██╔══██║██╔══██╗██╔═══╝
███████╗██║  ██║██║  ██║██║
╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝
"""
    )

    print(CYAN + "      Discord Username Finder v2")
    print(MAGENTA + "=" * 44)
    print()


# ==========================================================
# FILE HELPERS
# ==========================================================

def load_checked():
    if not os.path.exists(CHECKED_FILE):
        return set()

    checked = set()

    try:
        with open(
            CHECKED_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:
                username = line.strip()

                if username:
                    checked.add(username)

    except OSError as error:
        print(
            YELLOW
            + f"[!] Could not read {CHECKED_FILE}: {error}"
        )

    return checked


def save_checked(username):
    try:
        with open(
            CHECKED_FILE,
            "a",
            encoding="utf-8"
        ) as file:
            file.write(username + "\n")

    except OSError as error:
        print(
            YELLOW
            + f"[!] Could not save checked username: {error}"
        )


def save_available(username):
    try:
        with open(
            AVAILABLE_FILE,
            "a",
            encoding="utf-8"
        ) as file:
            file.write(username + "\n")

    except OSError as error:
        print(
            YELLOW
            + f"[!] Could not save valid username: {error}"
        )


# ==========================================================
# COUNTDOWN
# ==========================================================

def countdown(seconds):
    seconds = max(0, int(seconds))

    for remaining in range(
        seconds,
        0,
        -1
    ):
        message = (
            f"\r{YELLOW}"
            f"[RATE LIMIT] Resume in "
            f"{remaining:>4}s "
        )

        print(
            message,
            end="",
            flush=True
        )

        time.sleep(1)

    print(
        "\r"
        + CYAN
        + "[RATE LIMIT] Resuming...          "
    )


# ==========================================================
# WEBHOOK
# ==========================================================

def send_webhook(username):
    if (
        not WEBHOOK_URL
        or "PUT_YOUR" in WEBHOOK_URL
    ):
        print(
            YELLOW
            + "[WEBHOOK] No webhook configured."
        )
        return False

    payload = {
        "username": "LARP",
        "embeds": [
            {
                "title": "Username Found",
                "description": (
                    f"[+] `{username}` valid"
                ),
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
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code in (
            200,
            204
        ):
            print(
                CYAN
                + f"[WEBHOOK] Sent -> {username}"
            )
            return True

        if response.status_code == 429:
            try:
                data = response.json()
                retry_after = float(
                    data.get(
                        "retry_after",
                        5
                    )
                )
            except Exception:
                retry_after = 5

            print(
                YELLOW
                + "[WEBHOOK] Rate limited. "
                + f"Waiting {retry_after:.1f}s"
            )

            time.sleep(
                retry_after
                + RATE_LIMIT_BUFFER
            )

            return send_webhook(username)

        print(
            YELLOW
            + "[WEBHOOK ERROR] "
            + f"HTTP {response.status_code}"
        )

        return False

    except requests.RequestException as error:
        print(
            YELLOW
            + f"[WEBHOOK ERROR] {error}"
        )

        return False


# ==========================================================
# RATE LIMIT INFORMATION
# ==========================================================

def get_rate_limit_info(response):
    return {
        "limit":
            response.headers.get(
                "X-RateLimit-Limit"
            ),

        "remaining":
            response.headers.get(
                "X-RateLimit-Remaining"
            ),

        "reset_after":
            response.headers.get(
                "X-RateLimit-Reset-After"
            ),

        "scope":
            response.headers.get(
                "X-RateLimit-Scope"
            ),
    }


def proactive_cooldown(response):
    info = get_rate_limit_info(response)

    remaining = info["remaining"]
    reset_after = info["reset_after"]

    if remaining is None:
        return

    try:
        remaining = int(float(remaining))
    except ValueError:
        return

    if remaining > 1:
        return

    try:
        wait = float(
            reset_after or 3
        )
    except ValueError:
        wait = 3

    if wait <= 0:
        return

    print(
        YELLOW
        + "[LIMIT LOW] "
        + f"{remaining} remaining | "
        + f"cooldown {wait:.1f}s"
    )

    time.sleep(
        wait
        + RATE_LIMIT_BUFFER
    )


# ==========================================================
# CHECK USERNAME
# ==========================================================

def check_username(username):
    attempts = 0

    while True:
        attempts += 1

        try:
            response = session.post(
                CHECK_URL,
                json={
                    "username": username
                },
                timeout=REQUEST_TIMEOUT,
            )

        except requests.RequestException as error:
            print(
                YELLOW
                + f"[NETWORK] {username}: {error}"
            )

            wait = min(
                5 * attempts,
                30
            )

            print(
                YELLOW
                + f"[RETRY] Waiting {wait}s..."
            )

            time.sleep(wait)

            continue

        # ==================================================
        # RATE LIMITED
        # ==================================================

        if response.status_code == 429:
            retry_after = 10

            try:
                data = response.json()

                retry_after = float(
                    data.get(
                        "retry_after",
                        retry_after
                    )
                )

            except Exception:
                header_wait = response.headers.get(
                    "Retry-After"
                )

                if header_wait:
                    try:
                        retry_after = float(
                            header_wait
                        )
                    except ValueError:
                        pass

            retry_after += RATE_LIMIT_BUFFER

            print()

            countdown(
                retry_after
            )

            # Retry the SAME username.
            continue

        # ==================================================
        # OTHER HTTP ERROR
        # ==================================================

        if response.status_code != 200:
            print(
                YELLOW
                + f"[HTTP {response.status_code}] "
                + username
            )

            time.sleep(5)

            return None

        # ==================================================
        # JSON RESPONSE
        # ==================================================

        try:
            data = response.json()

        except ValueError:
            print(
                YELLOW
                + f"[INVALID RESPONSE] {username}"
            )

            return None

        taken = data.get("taken")

        # ==================================================
        # AVAILABLE
        # ==================================================

        if taken is False:
            print(
                GREEN
                + f"[+] {username} VALID"
            )

            save_checked(username)
            save_available(username)

            send_webhook(username)

            proactive_cooldown(
                response
            )

            return True

        # ==================================================
        # TAKEN
        # ==================================================

        if taken is True:
            print(
                RED
                + f"[-] {username} taken"
            )

            save_checked(username)

            proactive_cooldown(
                response
            )

            return False

        # ==================================================
        # UNKNOWN
        # ==================================================

        print(
            YELLOW
            + f"[?] {username} "
            + f"response: {data}"
        )

        return None


# ==========================================================
# USERNAME GENERATOR
# ==========================================================

def generate_usernames(checked):
    usernames = []

    for length in LENGTHS:

        combinations = itertools.product(
            CHARACTERS,
            repeat=length
        )

        current_length = []

        for combination in combinations:
            username = "".join(
                combination
            )

            if username not in checked:
                current_length.append(
                    username
                )

        # Randomize each length separately.
        random.shuffle(
            current_length
        )

        usernames.extend(
            current_length
        )

    return usernames


# ==========================================================
# STATUS
# ==========================================================

def show_status(
    checked_this_run,
    total_remaining,
    found,
    previously_checked
):
    print(
        DIM
        + WHITE
        + "    "
        + f"Run: {checked_this_run:,}"
        + " | "
        + f"Remaining: {total_remaining:,}"
        + " | "
        + GREEN
        + f"Found: {found}"
        + Style.RESET_ALL
        + DIM
        + WHITE
        + " | "
        + f"Previous: {previously_checked:,}"
    )


# ==========================================================
# MAIN
# ==========================================================

def main():
    banner()

    checked = load_checked()

    previously_checked = len(
        checked
    )

    print(
        WHITE
        + "Characters : "
        + CYAN
        + CHARACTERS
    )

    print(
        WHITE
        + "Lengths    : "
        + CYAN
        + ", ".join(
            map(str, LENGTHS)
        )
    )

    print(
        WHITE
        + "Checked DB : "
        + CYAN
        + f"{previously_checked:,}"
    )

    print(
        WHITE
        + "Delay      : "
        + CYAN
        + f"{MIN_DELAY}-{MAX_DELAY}s"
    )

    print(
        WHITE
        + "Mode       : "
        + GREEN
        + (
            "Stop after first valid"
            if STOP_AFTER_FIRST_VALID
            else "Continuous"
        )
    )

    print()
    print(MAGENTA + "=" * 44)
    print()

    print(
        CYAN
        + "[*] Generating unchecked usernames..."
    )

    usernames = generate_usernames(
        checked
    )

    total = len(
        usernames
    )

    print(
        CYAN
        + f"[*] {total:,} unchecked usernames loaded."
    )

    print(
        CYAN
        + "[*] Starting LARP..."
    )

    print()

    if total == 0:
        print(
            YELLOW
            + "[!] Nothing left to check."
        )
        return

    checked_this_run = 0
    found = 0

    try:
        for index, username in enumerate(
            usernames,
            start=1
        ):
            result = check_username(
                username
            )

            # Only count successfully classified
            # taken/available usernames.
            if result is not None:
                checked_this_run += 1

            if result is True:
                found += 1

                print()
                print(
                    GREEN
                    + "=" * 44
                )

                print(
                    GREEN
                    + "       VALID USERNAME FOUND"
                )

                print(
                    GREEN
                    + f"       Username: {username}"
                )

                print(
                    GREEN
                    + "=" * 44
                )

                print()

                if STOP_AFTER_FIRST_VALID:
                    break

            remaining = (
                total - index
            )

            show_status(
                checked_this_run,
                remaining,
                found,
                previously_checked,
            )

            # Normal randomized delay.
            delay = random.uniform(
                MIN_DELAY,
                MAX_DELAY
            )

            time.sleep(delay)

    except KeyboardInterrupt:
        print()
        print(
            YELLOW
            + "[!] LARP stopped by user."
        )

    finally:
        print()
        print(MAGENTA + "=" * 44)

        print(
            WHITE
            + "Checked this run : "
            + CYAN
            + f"{checked_this_run:,}"
        )

        print(
            WHITE
            + "Previously checked: "
            + CYAN
            + f"{previously_checked:,}"
        )

        print(
            WHITE
            + "Valid found      : "
            + GREEN
            + str(found)
        )

        print(MAGENTA + "=" * 44)


# ==========================================================
# START
# ==========================================================

if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print()
        print(
            RED
            + f"[FATAL] {error}"
        )

        sys.exit(1)
