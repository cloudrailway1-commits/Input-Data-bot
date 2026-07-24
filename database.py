import gspread
from google.oauth2.service_account import Credentials

from config import SPREADSHEET_ID, GOOGLE_CREDENTIALS

# ==========================================================
# GOOGLE SHEETS CONNECTION
# ==========================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_file(
    GOOGLE_CREDENTIALS,
    scopes=SCOPES,
)

client = gspread.authorize(creds)

worksheet = client.open_by_key(SPREADSHEET_ID).sheet1


# ==========================================================
# READ FUNCTIONS
# ==========================================================

def get_all_data():
    """Return all rows as dictionaries."""
    return worksheet.get_all_records()


def get_all_values():
    """Return all sheet values."""
    return worksheet.get_all_values()


def find_rfc(rfc: str):
    """
    Return row number of RFC.
    Return None if RFC does not exist.
    """
    values = worksheet.col_values(1)

    for row, value in enumerate(values, start=1):
        if value.strip().upper() == rfc.strip().upper():
            return row

    return None


def rfc_exists(rfc: str) -> bool:
    """Check if RFC ID exists in column A (regardless of technician status)."""
    return find_rfc(rfc) is not None


def is_rfc_available(rfc: str) -> bool:
    """Check if RFC exists AND is not already claimed/used by a technician."""
    rows = worksheet.get_all_values()
    if len(rows) <= 1:
        return False

    for row in rows[1:]:
        row_rfc = row[0].strip() if len(row) > 0 else ""
        tech = row[2].strip() if len(row) > 2 else ""

        if row_rfc.lower() == rfc.strip().lower():
            # Returns True only if Technician column is empty
            return tech == ""

    return False


def get_row(row: int):
    """Get values of a specific row."""
    return worksheet.row_values(row)


# ==========================================================
# WAREHOUSE & RFC FILTER FUNCTIONS
# ==========================================================

def get_all_warehouses():
    """
    Returns a list of unique Warehouse names (Column B).
    """
    rows = worksheet.get_all_values()
    if len(rows) <= 1:
        return []

    warehouses = []
    for row in rows[1:]:
        wh = row[1].strip() if len(row) > 1 else ""
        if wh and wh not in warehouses:
            warehouses.append(wh)

    return warehouses


def get_available_warehouses():
    """
    Returns unique Warehouses that have unfulfilled RFCs
    (where Technician in Column C is empty).
    """
    rows = worksheet.get_all_values()
    if len(rows) <= 1:
        return []

    available_warehouses = []
    for row in rows[1:]:
        rfc = row[0].strip() if len(row) > 0 else ""
        wh = row[1].strip() if len(row) > 1 else ""
        tech = row[2].strip() if len(row) > 2 else ""

        if rfc and not tech and wh:
            if wh not in available_warehouses:
                available_warehouses.append(wh)

    return available_warehouses


def get_available_rfcs_by_warehouse(warehouse_name: str):
    """
    Returns a list of RFC IDs for a specific Warehouse
    where Technician (Column C) is still empty.
    """
    rows = worksheet.get_all_values()
    if len(rows) <= 1:
        return []

    rfcs = []
    for row in rows[1:]:
        rfc = row[0].strip() if len(row) > 0 else ""
        wh = row[1].strip() if len(row) > 1 else ""
        tech = row[2].strip() if len(row) > 2 else ""

        if rfc and not tech and wh.lower() == warehouse_name.strip().lower():
            rfcs.append(rfc)

    return rfcs


def get_rfcs_by_warehouse(warehouse_name: str):
    """
    Returns all registered RFC IDs for a specific Warehouse.
    """
    rows = worksheet.get_all_values()
    if len(rows) <= 1:
        return []

    rfcs = []
    for row in rows[1:]:
        rfc = row[0].strip() if len(row) > 0 else ""
        wh = row[1].strip() if len(row) > 1 else ""

        if rfc and wh.lower() == warehouse_name.strip().lower():
            rfcs.append(rfc)

    return rfcs


def get_available_rfcs():
    """
    Returns all RFC tuples (RFC, Warehouse) where Technician (Column C) is empty.
    """
    rows = worksheet.get_all_values()
    if len(rows) <= 1:
        return []

    available = []
    for row in rows[1:]:
        rfc = row[0].strip() if len(row) > 0 else ""
        warehouse = row[1].strip() if len(row) > 1 else ""
        technician = row[2].strip() if len(row) > 2 else ""

        if rfc and not technician:
            available.append((rfc, warehouse))

    return available


def get_all_rfcs_with_warehouse():
    """
    Returns all registered RFC tuples (RFC, Warehouse).
    """
    rows = worksheet.get_all_values()
    if len(rows) <= 1:
        return []

    all_rfcs = []
    for row in rows[1:]:
        rfc = row[0].strip() if len(row) > 0 else ""
        warehouse = row[1].strip() if len(row) > 1 else ""
        if rfc:
            all_rfcs.append((rfc, warehouse))

    return all_rfcs


# ==========================================================
# CREATE FUNCTIONS
# ==========================================================

def add_rfc(rfc: str, warehouse: str, engineer_name: str = ""):
    """
    Add a new RFC row under a specific Warehouse Category.
    """
    worksheet.append_row([
        rfc.upper(),        # A = RFC
        warehouse,          # B = Warehouse / Category
        "",                 # C = Technician
        "",                 # D = Drop Core
        "",                 # E = Precon50
        "",                 # F = Precon60
        "",                 # G = Precon70
        "",                 # H = Precon75
        "",                 # I = Precon80
        "",                 # J = Precon85
        "",                 # K = Precon100
        "",                 # L = Precon120
        "",                 # M = Precon125
        "",                 # N = Precon130
        "",                 # O = Precon135
        "",                 # P = Precon150
        "",                 # Q = Precon200
        "",                 # R = Precon250
        "",                 # S = Clamp-hook
        "",                 # T = S-Clamp S
        "",                 # U = SOC-ILS
        "",                 # V = SOC-FUJ
        "",                 # W = SOC-SUM
        "",                 # X = SN ONT
        "",                 # Y = SN STB
    ])


# ==========================================================
# UPDATE FUNCTIONS
# ==========================================================

def update_cell(row: int, col: int, value):
    """Update a single cell."""
    worksheet.update_cell(row, col, value)


def update_row_answers(row: int, technician: str, answers: list):
    """
    Update technician name (Column C) and material answers (Column D onwards).
    """
    # Column C = Technician Name
    worksheet.update_cell(row, 3, technician)

    # Column D onwards = Material Answers
    for i, answer in enumerate(answers):
        worksheet.update_cell(
            row,
            4 + i,
            answer,
        )


# ==========================================================
# DELETE FUNCTIONS
# ==========================================================

def delete_rfc(rfc: str):
    """Delete an RFC row by RFC ID."""
    row = find_rfc(rfc)

    if row:
        worksheet.delete_rows(row)
        return True

    return False


if __name__ == "__main__":
    print("=" * 50)
    print("Google Sheets Connected Successfully")
    print("=" * 50)

    print("Worksheet :", worksheet.title)
    print("Rows      :", worksheet.row_count)
    print("Columns   :", worksheet.col_count)
    
