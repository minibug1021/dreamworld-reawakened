"""Trainer Club accounts and the Game Sync IDs linked to them (an SQLite database)."""
import sqlite3
from typing import cast

from config import SAVE_DIR
from game_sync_server.entralinked.utility.sqlite_store import SQLiteStore
from utils.models import Account, Privacy

# generate_password_hash("testpass")
_TEST_PASSWORD_HASH = ("scrypt:32768:8:1$jZODhHVaqfKNahLu$671ff90e1738953e87edfa84abcc5fe3148409a7b37a207b9bb15fb02a96062b"
                       "bfe1195be50503b1c3058cdbfbf3a9c9d824beace12898add8ae2e55fa83e99a")


class AccountManager(SQLiteStore):
    """The accounts table (one row per login) and account_gscds (gscd -> owner)."""

    SCHEMA = (
        """
        CREATE TABLE IF NOT EXISTS accounts (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            email TEXT NOT NULL,
            country INTEGER,
            birth_month INTEGER,
            pgl_privacy TEXT,
            dw_privacy TEXT,
            activated INTEGER NOT NULL DEFAULT 0,
            activation_token TEXT,
            active_gscd TEXT,
            last_daily_bonus_date TEXT,
            shows_shiny INTEGER NOT NULL DEFAULT 1,
            registered INTEGER NOT NULL DEFAULT 0
        )""",
        """
        CREATE TABLE IF NOT EXISTS account_gscds (
            gscd TEXT PRIMARY KEY,
            username TEXT NOT NULL
        )""",
        # activated test accounts
        f"""
        INSERT INTO accounts (username, password_hash, email, country, birth_month, pgl_privacy, dw_privacy, activated)
        SELECT column1, '{_TEST_PASSWORD_HASH}', 'a@example.com', 1, 1, 'everyone', 'everyone', 1
        FROM (VALUES ('Test'), ('TestMulti'))
        WHERE NOT EXISTS (SELECT 1 FROM accounts)""",
    )

    def _fetch_one(self, query: str, *params: object) -> sqlite3.Row | None:
        return self._conn.execute(query, params).fetchone()

    def _fetch_account(self, query: str, *params: object) -> Account | None:
        row = self._fetch_one(query, *params)
        return cast(Account, dict(row)) if row else None

    def _execute(self, query: str, *params: object) -> None:
        with self._conn:
            self._conn.execute(query, params)

    def count_accounts(self) -> int:
        """Return the number of accounts."""
        return self._conn.execute("SELECT COUNT(*) FROM accounts WHERE registered == 1").fetchone()[0]

    def create_account(self, username: str, password_hash: str, email: str, country: int,
                       birth_month: int, pgl_privacy: Privacy, dw_privacy: Privacy,
                       activation_token: str) -> bool:
        """Create an account that is not activated yet.

        Return False and create nothing if the username is taken.
        """
        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO accounts
                    (username, password_hash, email, country, birth_month, pgl_privacy, dw_privacy, activation_token)
                SELECT ?, ?, ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (SELECT 1 FROM accounts WHERE username = ? COLLATE NOCASE)
                """,
                (username, password_hash, email, country, birth_month, pgl_privacy, dw_privacy, activation_token,
                 username),
            )
        return cursor.rowcount == 1

    def get_account_by_activation_token(self, token: str) -> Account | None:
        """Return the account with this activation token, if any."""
        return self._fetch_account("SELECT * FROM accounts WHERE activation_token = ?", token)

    def get_account_by_username(self, username: str | None) -> Account | None:
        """Return the account with this username, or None if there is none.

        The match ignores case.
        """
        if not username:
            return None
        return self._fetch_account("SELECT * FROM accounts WHERE username = ? COLLATE NOCASE", username)

    def activate_account(self, token: str) -> None:
        """Activate the account with this activation token."""
        self._execute("UPDATE accounts SET activated = 1 WHERE activation_token = ?", token)

    def get_country_id(self, username: str | None) -> int | None:
        """Return the country the account signed up with.

        Return None if there's no such account or it has no country.
        """
        account = self.get_account_by_username(username)
        return account["country"] if account else None

    def get_shows_shiny(self, username: str | None) -> bool:
        """Whether shiny Pokémon should render for this account.

        Defaults to True.
        """
        account = self.get_account_by_username(username)
        return bool(account["shows_shiny"]) if account else True

    def mark_registered(self, username: str) -> None:
        """Record that the account has registered their username."""
        self._execute("UPDATE accounts SET registered = 1 WHERE username = ?", username)

    def get_gscds_for_account(self, username: str) -> list[str]:
        """Return the account's linked Game Sync IDs, oldest link first."""
        cursor = self._conn.execute("SELECT gscd FROM account_gscds WHERE username = ? ORDER BY rowid", (username,))
        return [row["gscd"] for row in cursor.fetchall()]

    def get_gscd_owner(self, gscd: str) -> str | None:
        """Return the username a Game Sync ID is linked to, if any."""
        row = self._fetch_one("SELECT username FROM account_gscds WHERE gscd = ?", gscd)
        return row["username"] if row else None

    def link_gscd(self, username: str, gscd: str) -> None:
        """Link a Game Sync ID to an account.

        The first one linked becomes the account's active one.
        """
        with self._conn:
            self._conn.execute("INSERT OR IGNORE INTO account_gscds (gscd, username) VALUES (?, ?)", (gscd, username))
            self._conn.execute(
                "UPDATE accounts SET active_gscd = ? WHERE username = ? AND active_gscd IS NULL",
                (gscd, username),
            )

    def claim_daily_bonus(self, username: str, today: str) -> bool:
        """Claim `username`'s daily bonus for `today`.

        Return True (and record `today`) the first time this is called for `username` on a
        given day. False if today's bonus was already claimed.
        """
        with self._conn:
            cursor = self._conn.execute(
                """UPDATE accounts SET last_daily_bonus_date = ?
                   WHERE username = ? AND last_daily_bonus_date IS NOT ?""",
                (today, username, today))
        return cursor.rowcount == 1


accounts = AccountManager(SAVE_DIR / "pokemon_saves.db")
