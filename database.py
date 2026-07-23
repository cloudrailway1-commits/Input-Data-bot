import logging
import gspread
from google.oauth2.service_account import Credentials
from config import GOOGLE_CREDENTIALS

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_NAME = "Fieldwork_Material_Database"
WORKSHEET_NAME = "RFC_Data"


def get_worksheet():
    try:
        creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open(SPREADSHEET_NAME)
        return spreadsheet.worksheet(WORKSHEET_NAME)
    except Exception as e:
        logger.error(f"Failed to connect to Google Sheets: {e}")
        raise e


def get_all_rows() -> list[dict]:
    """Fetches all records as dictionaries with normalized lower_snake_case keys."""
    try:
        sheet = get_worksheet()
        records = sheet.get_all_records()
        normalized_records = []
        for row in records:
            clean_row = {}
            for k, v in row.items():
                clean_key = str(k).strip().lower().replace(" ", "_").replace("/", "_")
                clean_row[clean_key] = str(v).strip() if v is not None else ""
            normalized_records.append(clean_row)
        return normalized_records
    except Exception as e:
        logger.error(f"Error fetching rows from database: {e}")
        return []


def _extract_warehouse(row: dict) -> str:
    """Helper to extract warehouse value regardless of column header variations."""
    for key in ["warehouse", "location", "so_location", "warehouse___so_location", "so"]:
        if key in row and row[key]:
            return row[key].upper()
    return ""


def _extract_rfc_id(row: dict) -> str:
    """Helper to extract RFC ID value regardless of column header variations."""
    for key in ["rfc_id", "rfc", "rfc_number", "id"]:
        if key in row and row[key]:
            return row[key].upper()
    return ""


def rfc_exists(rfc: str) -> bool:
    try:
        target = str(rfc).strip().upper()
        records = get_all_rows()
        for row in records:
            if _extract_rfc_id(row) == target:
                return True
        return False
    except Exception as e:
        logger.error(f"Error checking if RFC exists: {e}")
        return False


def add_rfc(rfc: str, warehouse: str, engineer_name: str) -> bool:
    try:
        sheet = get_worksheet()
        # Appends directly across Columns A to E
        sheet.append_row([
            str(rfc).strip().upper(),
            str(warehouse).strip().upper(),
            str(engineer_name).strip(),
            "",
            "AVAILABLE"
        ])
        logger.info(f"Successfully added RFC: {rfc} under {warehouse}")
        return True
    except Exception as e:
        logger.error(f"Error adding RFC {rfc}: {e}")
        return False


def get_rfcs_by_warehouse(warehouse: str) -> list[str]:
    records = get_all_rows()
    rfcs = []
    target_wh = str(warehouse).strip().upper()

    for row in records:
        row_wh = _extract_warehouse(row)
        rfc_id = _extract_rfc_id(row)
        if row_wh == target_wh and rfc_id:
            rfcs.append(rfc_id)

    return rfcs


def get_available_rfcs_by_warehouse(warehouse: str) -> list[str]:
    records = get_all_rows()
    available = []
    target_wh = str(warehouse).strip().upper()

    for row in records:
        row_wh = _extract_warehouse(row)
        status = row.get("status", "").upper()
        tech = row.get("technician", "")
        rfc_id = _extract_rfc_id(row)

        if row_wh == target_wh and status != "COMPLETED" and not tech:
            if rfc_id:
                available.append(rfc_id)

    return available


def find_rfc(rfc: str):
    try:
        target = str(rfc).strip().upper()
        records = get_all_rows()
        for idx, row in enumerate(records):
            if _extract_rfc_id(row) == target:
                return idx + 2  # Row offset for header
        return None
    except Exception as e:
        logger.error(f"Error finding RFC {rfc}: {e}")
        return None


def update_row_answers(row: int, technician: str, answers: list[str]) -> bool:
    try:
        sheet = get_worksheet()
        sheet.update_cell(row, 4, str(technician))
        sheet.update_cell(row, 5, "COMPLETED")

        for offset, answer in enumerate(answers):
            sheet.update_cell(row, 6 + offset, str(answer))

        logger.info(f"Updated row {row} with technician answers.")
        return True
    except Exception as e:
        logger.error(f"Error updating row {row}: {e}")
        raise e
