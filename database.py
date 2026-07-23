import logging
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_NAME = "Fieldwork_Material_Database"
WORKSHEET_NAME = "RFC_Data"

def get_worksheet():
    try:
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open(SPREADSHEET_NAME)
        return spreadsheet.worksheet(WORKSHEET_NAME)
    except Exception as e:
        logger.error(f"Failed to connect to Google Sheets: {e}")
        raise e

def get_all_rows() -> list[dict]:
    try:
        sheet = get_worksheet()
        return sheet.get_all_records()
    except Exception as e:
        logger.error(f"Error fetching rows from database: {e}")
        return []

def rfc_exists(rfc: str) -> bool:
    try:
        target = str(rfc).strip().upper()
        records = get_all_rows()
        for row in records:
            for key, val in row.items():
                if str(key).strip().lower() in ["rfc id", "rfc", "rfc_id"]:
                    if str(val).strip().upper() == target:
                        return True
        return False
    except Exception as e:
        logger.error(f"Error checking if RFC exists: {e}")
        return False

def add_rfc(rfc: str, warehouse: str, engineer_name: str) -> bool:
    try:
        sheet = get_worksheet()
        sheet.append_row([str(rfc).strip().upper(), str(warehouse).strip().upper(), str(engineer_name).strip(), "", "AVAILABLE"])
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
        row_wh = ""
        rfc_id = ""
        for key, val in row.items():
            clean_key = str(key).strip().lower()
            if clean_key == "warehouse":
                row_wh = str(val).strip().upper()
            elif clean_key in ["rfc id", "rfc", "rfc_id"]:
                rfc_id = str(val).strip().upper()
        if row_wh == target_wh and rfc_id:
            rfcs.append(rfc_id)
    return rfcs

def get_available_rfcs_by_warehouse(warehouse: str) -> list[str]:
    records = get_all_rows()
    available = []
    target_wh = str(warehouse).strip().upper()
    for row in records:
        row_wh = ""
        tech = ""
        status = ""
        rfc_id = ""
        for key, val in row.items():
            clean_key = str(key).strip().lower()
            if clean_key == "warehouse":
                row_wh = str(val).strip().upper()
            elif clean_key == "technician":
                tech = str(val).strip()
            elif clean_key == "status":
                status = str(val).strip().upper()
            elif clean_key in ["rfc id", "rfc", "rfc_id"]:
                rfc_id = str(val).strip().upper()

        if row_wh == target_wh and (not tech) and status != "COMPLETED":
            if rfc_id:
                available.append(rfc_id)
    return available

def find_rfc(rfc: str):
    try:
        target = str(rfc).strip().upper()
        records = get_all_rows()
        for idx, row in enumerate(records):
            for key, val in row.items():
                if str(key).strip().lower() in ["rfc id", "rfc", "rfc_id"]:
                    if str(val).strip().upper() == target:
                        return idx + 2
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
