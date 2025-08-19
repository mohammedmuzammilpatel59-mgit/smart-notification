from __future__ import annotations

import os
from typing import List

try:
    import gspread
    from google.oauth2.service_account import Credentials
except Exception:  # optional at runtime
    gspread = None
    Credentials = None  # type: ignore


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


def append_row_to_sheet(
    spreadsheet_id: str,
    worksheet_name: str,
    row_values: List[str],
    service_account_json_path: str | None = None,
) -> None:
    if gspread is None or Credentials is None:
        raise RuntimeError("Google Sheets dependencies not available (gspread/google-auth)")

    creds_path = service_account_json_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not os.path.exists(creds_path):
        raise FileNotFoundError(
            "Service account JSON not found. Set GOOGLE_APPLICATION_CREDENTIALS or pass path."
        )

    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    sh = client.open_by_key(spreadsheet_id)
    try:
        ws = sh.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=worksheet_name, rows=100, cols=10)
    ws.append_row(row_values)  # type: ignore[arg-type]