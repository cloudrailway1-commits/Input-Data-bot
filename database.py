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
# SHEET STRUCTURE
# ==========================================================
#
# Column A = RFC
# Column B = Warehouse Engineer
# Column C = Technician
# Column D = Drop Core
# Column E = Precon50
# Column F = Precon60
# Column G = Precon70
# Column H = Precon75
# Column I = Precon80
# Column J = Precon85
# Column K = Precon100
# Column L = Precon120
# Column M = Precon125
# Column N = Precon130
# Column O = Precon135
# Column P = Precon150
# Column Q = Precon200
# Column R = Precon250
# Column S = Clamp-hook
# Column T = S-Clamp S
# Column U = SOC-ILS
# Column V = SOC-FUJ
# Column W = SOC-SUM
# Column X = SN ONT
# Column Y = SN STB
#
# ==========================================================


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
        if value.strip() == rfc.strip():
            return row

    return None


def rfc_exists(rfc: str):
    return find_rfc(rfc) is not None


def get_row(row: int):
    return worksheet.row_values(row)


# ==========================================================
# CREATE FUNCTIONS
# ==========================================================

def add_rfc(rfc: str, warehouse_name: str):
    """
    Add new RFC row.
    """

    worksheet.append_row([
        rfc,               # A
        warehouse_name,    # B
        "",                # C Technician
        "",                # D Drop Core
        "",                # E Precon50
        "",                # F Precon60
        "",                # G Precon70
        "",                # H Precon75
        "",                # I Precon80
        "",                # J Precon85
        "",                # K Precon100
        "",                # L Precon120
        "",                # M Precon125
        "",                # N Precon130
        "",                # O Precon135
        "",                # P Precon150
        "",                # Q Precon200
        "",                # R Precon250
        "",                # S Clamp-hook
        "",                # T S-Clamp S
        "",                # U SOC-ILS
        "",                # V SOC-FUJ
        "",                # W SOC-SUM
        "",                # X SN ONT
        "",                # Y SN STB
    ])


# ==========================================================
# UPDATE FUNCTIONS
# ==========================================================

def update_cell(row: int, col: int, value):
    """
    Update one cell.
    """
    worksheet.update_cell(row, col, value)


def update_row_answers(row: int, technician: str, answers: list):
    """
    Update technician name and all material answers.
    """

    # Column C
    worksheet.update_cell(row, 3, technician)

    # Column D onwards
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
    """
    Delete RFC row.
    """

    row = find_rfc(rfc)

    if row:
        worksheet.delete_rows(row)
        return True

    return False


# ==========================================================
# DEBUG
# ==========================================================

def print_sheet():
    for row in worksheet.get_all_values():
        print(row)


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 50)
    print("Google Sheets Connected Successfully")
    print("=" * 50)

    print("Worksheet :", worksheet.title)
    print("Rows      :", worksheet.row_count)
    print("Columns   :", worksheet.col_count)