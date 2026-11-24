"""Reads the HMS database for state evidence, through the read-only account."""
import pymysql
from config import DB

def row_exists(sql, args=()):
    conn = pymysql.connect(**DB)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()
    finally:
        conn.close()

def marker_present(table, id_col, id_val, text_col, marker):
    row = row_exists(f"SELECT {text_col} FROM {table} WHERE {id_col}=%s", (id_val,))
    return row is not None and marker in str(row[0])

def first_login(table, id_col, email_col="email", password_col="password"):
    """Looks up a real (id, email, password) row from the live database for a role table
    (nurse, pharmacist, accountant, ...), so the experiment doesn't need a guessed/hardcoded
    account. Returns None if the table is empty."""
    row = row_exists(f"SELECT {id_col}, {email_col}, {password_col} FROM {table} ORDER BY {id_col} LIMIT 1")
    return row  # (id, email, password) or None

def resolve_dynamic_accounts(accounts):
    """Fills in any ACCOUNTS entry marked dynamic=True (nurse1/pharmacist1/accountant1) by
    querying the live database for a real row, instead of a guessed email/password. Mutates
    and returns `accounts`. Safe to call more than once -- already-resolved entries are skipped."""
    for key, acc in accounts.items():
        if acc.get("dynamic"):
            row = first_login(acc["dynamic_table"], acc["dynamic_id_col"])
            if row is None:
                raise RuntimeError(f"no rows in `{acc['dynamic_table']}` to resolve account {key!r} from")
            acc["id"], acc["email"], acc["password"] = row
            acc["dynamic"] = False  # resolved; don't re-query every call
    return accounts
