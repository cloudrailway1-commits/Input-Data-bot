import logging
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

# ==========================================================
# GOOGLE SHEETS SETUP
# ==========================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_NAME = "Fieldwork_Material_Database"
WORKSHEET_NAME = "RFC_Data"


def get_worksheet():
    """Connects to Google Sheets API using google-auth and returns target worksheet."""
    try:
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open(SPREADSHEET_NAME)
        return spreadsheet.worksheet(WORKSHEET_NAME)
    except Exception as e:
        logger.error(f"Failed to connect to Google Sheets: {e}")
        raise e


# ==========================================================
# DATABASE HELPER & CORE FUNCTIONS
# ==========================================================

def get_all_rows() -> list[dict]:
    """Fetches all records from the Google Sheet as a list of dictionaries."""
    try:
        sheet = get_worksheet()
        return sheet.get_all_records()
    except Exception as e:
        logger.error(f"Error fetching rows from database: {e}")
        return []


def rfc_exists(rfc: str) -> bool:
    """Checks if an RFC ID already exists in the database (case-insensitive)."""
    try:
        sheet = get_worksheet()
        cell = sheet.find(rfc.strip().upper())
        # In gspread v6+, find() returns None if missing
        return cell is not None
    except Exception as e:
        logger.error(f"Error checking if RFC exists: {e}")
        return False


def add_rfc(rfc: str, warehouse: str, engineer_name: str) -> bool:
    """Registers a new RFC under a specific Warehouse."""
    try:
        sheet = get_worksheet()
        # Row format: [RFC ID, Warehouse, Engineer, Technician, Status]
        sheet.append_row([rfc.strip().upper(), warehouse.strip().upper(), engineer_name.strip(), "", "AVAILABLE"])
        logger.info(f"Successfully added RFC: {rfc} under {warehouse}")
        return True
    except Exception as e:
        logger.error(f"Error adding RFC {rfc}: {e}")
        return False


def get_rfcs_by_warehouse(warehouse: str) -> list[str]:
    """Returns all RFC IDs registered under a specific warehouse."""
    records = get_all_rows()
    rfcs = []
    
    for row in records:
        row_wh = ""
        rfc_id = ""
        for key, val in row.items():
            clean_key = str(key).strip().lower()
            if clean_key == "warehouse":
                row_wh = str(val).strip().upper()
            elif clean_key in ["rfc id", "rfc", "rfc_id"]:
                rfc_id = str(val).strip().upper()

        if row_wh == warehouse.strip().upper() and rfc_id:
            rfcs.append(rfc_id)

    return rfcs


def get_available_rfcs_by_warehouse(warehouse: str) -> list[str]:
    """
    Returns active RFCs for a warehouse that have NOT been completed or assigned to a technician.
    Header matching is normalized to prevent sheet whitespace mismatches.
    """
    records = get_all_rows()
    available = []
    
    for row in records:
        row_wh = ""
        tech = ""
        status = ""
        rfc_id = ""

        # Normalize dictionary keys from get_all_records()
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

        # RFC is available if warehouse matches, technician is empty, and status isn't COMPLETED
        if row_wh == warehouse.strip().upper() and (not tech) and status != "COMPLETED":
            if rfc_id:
                available.append(rfc_id)
            
    return available


def find_rfc(rfc: str):
    """Finds and returns the row index (1-based) in Google Sheets for a given RFC ID."""
    try:
        sheet = get_worksheet()
        cell = sheet.find(rfc.strip().upper())
        return cell.row if cell else None
    except Exception as e:
        logger.error(f"Error finding RFC {rfc}: {e}")
        return None


def update_row_answers(row: int, technician: str, answers: list[str]) -> bool:
    """Updates the database row when a Technician submits a report."""
    try:
        sheet = get_worksheet()
        
        # Column 4: Technician Name
        # Column 5: Status ('COMPLETED')
        sheet.update_cell(row, 4, technician)
        sheet.update_cell(row, 5, "COMPLETED")

        # Write question responses starting from Column 6 onwards
        for offset, answer in enumerate(answers):
            sheet.update_cell(row, 6 + offset, str(answer))

        logger.info(f"Updated row {row} with technician answers.")
        return True

    except Exception as e:
        logger.error(f"Error updating row {row}: {e}")
        raise e
