import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials

logger = logging.getLogger(__name__)

# ==========================================================
# GOOGLE SHEETS SETUP
# ==========================================================

# Define Google Sheets scope and credentials
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# Name of your Google Sheet
SPREADSHEET_NAME = "Fieldwork_Material_Database"
WORKSHEET_NAME = "RFC_Data"

def get_worksheet():
    """Connects to Google Sheets API and returns the target worksheet."""
    try:
        # Load credentials from JSON keyfile
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
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
    """Checks if an RFC ID already exists in the database."""
    try:
        sheet = get_worksheet()
        cell = sheet.find(rfc.upper())
        return cell is not None
    except gspread.exceptions.CellNotFound:
        return False
    except Exception as e:
        logger.error(f"Error checking if RFC exists: {e}")
        return False


def add_rfc(rfc: str, warehouse: str, engineer_name: str) -> bool:
    """
    Registers a new RFC under a specific Warehouse.
    Expected Sheet Columns: [RFC ID, Warehouse, Engineer, Technician, Status, Answers...]
    """
    try:
        sheet = get_worksheet()
        # Append new RFC record (Technician & Status start empty)
        sheet.append_row([rfc.upper(), warehouse, engineer_name, "", "AVAILABLE"])
        logger.info(f"Successfully added RFC: {rfc} under {warehouse}")
        return True
    except Exception as e:
        logger.error(f"Error adding RFC {rfc}: {e}")
        return False


def get_rfcs_by_warehouse(warehouse: str) -> list[str]:
    """Returns all RFC IDs registered under a specific warehouse."""
    records = get_all_rows()
    return [
        str(row["RFC ID"]) for row in records 
        if str(row.get("Warehouse", "")).upper() == warehouse.upper()
    ]


def get_available_rfcs_by_warehouse(warehouse: str) -> list[str]:
    """
    Single-Use Enforcement:
    Returns ONLY active RFCs under the given warehouse that have NOT 
    been submitted by a technician yet (i.e. Technician column is empty or Status is AVAILABLE).
    """
    records = get_all_rows()
    available = []
    
    for row in records:
        row_wh = str(row.get("Warehouse", "")).strip().upper()
        tech = str(row.get("Technician", "")).strip()
        status = str(row.get("Status", "")).strip().upper()

        if row_wh == warehouse.upper() and (not tech) and status != "COMPLETED":
            available.append(str(row["RFC ID"]))
            
    return available


def find_rfc(rfc: str):
    """
    Finds and returns the 1-based row index in Google Sheets for a given RFC.
    Returns row index (int) or None if not found.
    """
    try:
        sheet = get_worksheet()
        cell = sheet.find(rfc.upper())
        return cell.row if cell else None
    except Exception as e:
        logger.error(f"Error finding RFC {rfc}: {e}")
        return None


def update_row_answers(row: int, technician: str, answers: list[str]) -> bool:
    """
    Updates the database row when a Technician submits a report.
    Sets Technician Name, Status to 'COMPLETED', and fills in question answers.
    """
    try:
        sheet = get_worksheet()
        
        # Column 4: Technician Name
        # Column 5: Status ('COMPLETED')
        sheet.update_cell(row, 4, technician)
        sheet.update_cell(row, 5, "COMPLETED")

        # Starting from Column 6 onwards: Write all question answers
        for offset, answer in enumerate(answers):
            sheet.update_cell(row, 6 + offset, str(answer))

        logger.info(f"Updated row {row} with technician answers.")
        return True

    except Exception as e:
        logger.error(f"Error updating row {row}: {e}")
        raise e
