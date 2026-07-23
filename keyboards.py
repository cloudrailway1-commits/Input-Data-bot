from telegram import ReplyKeyboardMarkup

# ==========================================================
# FIXED WAREHOUSE LIST
# ==========================================================

FIXED_WAREHOUSES = [
    "ACEH",
    "SO LANGSA",
    "SO LHOKSEUMAWE",
    "SO MEULABOH",
    "SO TAPAKTUAN",
    "SO TAKENGON",
    "SO SIGLI",
    "MEDAN",
    "SO BINJAI",
    "SO PADANG BULAN",
    "SO PUBA",
    "SO SPM",
    "SO SKI",
    "SO TJR",
    "SO TJM",
    "SO LBP",
    "SUMUT",
    "SO KABANAJAHE",
    "SO KISARAN",
    "SO SIDEMPUAN",
    "SO PMTG SIANTAR",
    "SO RANTAU PRAPAT",
    "SO SIBLOGA",
]


# ==========================================================
# STATIC KEYBOARDS
# ==========================================================

ROLE_KEYBOARD = ReplyKeyboardMarkup(
    [["🏭 Warehouse Engineer"], ["🛠 Technician"]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

AFTER_REGISTER_KEYBOARD = ReplyKeyboardMarkup(
    [["➕ Add More RFC"], ["⬅️ Back to Main Menu"]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

AFTER_REPORT_KEYBOARD = ReplyKeyboardMarkup(
    [["📋 Submit Another Report"], ["⬅️ Back to Main Menu"]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

SAME_RFC_KEYBOARD = ReplyKeyboardMarkup(
    [["📑 Use Same RFC"], ["📄 Use Different RFC"], ["⬅️ Back to Main Menu"]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

PREVIEW_KEYBOARD = ReplyKeyboardMarkup(
    [["✅ Confirm & Submit"], ["✏️ Edit Answers", "❌ Cancel Report"]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

CANCEL_EDIT_KEYBOARD = ReplyKeyboardMarkup(
    [["❌ Cancel Editing"]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

RFC_NOT_FOUND_KEYBOARD = ReplyKeyboardMarkup(
    [["✍️ Try Another RFC"], ["⬅️ Back to Main Menu"]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

NO_RFC_KEYBOARD = ReplyKeyboardMarkup(
    [["⬅️ Back to Main Menu"]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

FINISH_KEYBOARD = ReplyKeyboardMarkup(
    [["🔄 New Report"], ["❌ Exit"]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


# ==========================================================
# DYNAMIC KEYBOARD HELPERS
# ==========================================================

def get_warehouse_keyboard(warehouses_list: list = None):
    """
    Generates a 2-column reply keyboard listing warehouses.
    Defaults to FIXED_WAREHOUSES if no list is passed.
    """
    items = warehouses_list if warehouses_list else FIXED_WAREHOUSES

    # Arrange buttons 2 per row
    buttons = []
    for i in range(0, len(items), 2):
        row = [items[i]]
        if i + 1 < len(items):
            row.append(items[i + 1])
        buttons.append(row)

    buttons.append(["⬅️ Back to Main Menu"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)


def get_rfc_keyboard(rfcs_list: list):
    """Generates a reply keyboard listing RFC IDs for a selected warehouse."""
    buttons = [[rfc] for rfc in rfcs_list]
    buttons.append(["⬅️ Back to Main Menu"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
