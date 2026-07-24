import logging
import time
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

# ==========================================================
# Google Sheets Credentials & Scope Setup
# ==========================================================
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Update path to your service account JSON file if different
CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_NAME = "Your Sheet Name"  # Change to your actual Google Sheet title

try:
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPE)
    gc = gspread.authorize(creds)
    sheet = gc.open(SPREADSHEET_NAME).sheet1
except Exception as e:
    logger.error(f"Failed to initialize Google Sheets connection: {e}")
    sheet = None

# ==========================================================
# In-Memory Cache Engine
# ==========================================================
_SHEET_CACHE = None
_LAST_CACHE_TIME = 0
CACHE_TTL = 60  # Cache duration in seconds


def get_all_sheet_data(force_refresh=False):
    """Fetches all sheet rows in a single batch call and caches in memory."""
    global _SHEET_CACHE, _LAST_CACHE_TIME

    current_time = time.time()

    if (
        force_refresh
        or _SHEET_CACHE is None
        or (current_time - _LAST_CACHE_TIME > CACHE_TTL)
    ):
        try:
            if sheet is not None:
                # Single API request to grab all spreadsheet values
                _SHEET_CACHE = sheet.get_all_values()
                _LAST_CACHE_TIME = current_time
            else:
                _SHEET_CACHE = []
        except Exception as e:
            logger.error(f"Error fetching data from Google Sheets: {e}")
            if _SHEET_CACHE is None:
                _SHEET_CACHE = []

    return _SHEET_CACHE


# ==========================================================
# Database Operations (Exact Case Preserved for Primary Keys)
# ==========================================================

def get_available_rfcs_by_warehouse(warehouse_name):
    """Filters active RFCs directly from RAM cache in milliseconds."""
    all_rows = get_all_sheet_data()
    available_rfcs = []

    # Columns: Row[0]=RFC, Row[1]=Warehouse, Row[2]=Status
    for row in all_rows[1:]:  # Skip header row
        if len(row) >= 3:
            rfc_id = row[0].strip()
            wh = row[1].strip()
            status = row[2].strip()

            if wh == warehouse_name and status.lower() == "available":
                available_rfcs.append(rfc_id)

    return available_rfcs


def rfc_exists(rfc):
    """Checks if an RFC ID exists in sheet (Exact case match)."""
    all_rows = get_all_sheet_data()
    rfc_clean = rfc.strip()

    for row in all_rows[1:]:
        if len(row) >= 1 and row[0].strip() == rfc_clean:
            return True
    return False


def is_rfc_available(rfc):
    """Checks if an RFC is marked as available (Exact case match)."""
    all_rows = get_all_sheet_data()
    rfc_clean = rfc.strip()

    for row in all_rows[1:]:
        if len(row) >= 3:
            if row[0].strip() == rfc_clean and row[2].strip().lower() == "available":
                return True
    return False


def add_rfc(rfc, warehouse, engineer_name):
    """Appends new RFC to Google Sheet preserving exact uppercase/lowercase entry."""
    rfc_clean = rfc.strip()
    if sheet:
        sheet.append_row([rfc_clean, warehouse, "available", engineer_name])
    
    # Invalidate cache to reflect changes immediately
    get_all_sheet_data(force_refresh=True)


def delete_rfc(rfc):
    """Deletes an RFC record from Google Sheets."""
    all_rows = get_all_sheet_data()
    rfc_clean = rfc.strip()

    for i, row in enumerate(all_rows[1:], start=2):  # 1-indexed, header is row 1
        if len(row) >= 1 and row[0].strip() == rfc_clean:
            if sheet:
                sheet.delete_rows(i)
            get_all_sheet_data(force_refresh=True)
            break


def find_rfc(rfc):
    """Returns row index for given RFC ID (Exact case match)."""
    all_rows = get_all_sheet_data()
    rfc_clean = rfc.strip()

    for i, row in enumerate(all_rows[1:], start=2):
        if len(row) >= 1 and row[0].strip() == rfc_clean:
            return i
    return None


def update_row_answers(row, technician, answers):
    """Submits report answers and marks RFC status as completed."""
    if sheet:
        # Col 3: Status, Col 4: Technician Name, Col 5+: Answers
        sheet.update_cell(row, 3, "completed")
        sheet.update_cell(row, 4, technician)

        for idx, ans in enumerate(answers, start=5):
            sheet.update_cell(row, idx, ans)

    get_all_sheet_data(force_refresh=True)
