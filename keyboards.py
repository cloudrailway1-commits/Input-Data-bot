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
    [
        ["➕ Add More RFC"],
        ["🏬 Change Warehouse", "⬅️ Back to Main Menu"],
        ["🏁 Finish Session"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

AFTER_REPORT_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📋 Submit Another Report"],
        ["🏬 Change Warehouse", "⬅️ Back to Main Menu"],
        ["🏁 Finish Session"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

SAME_RFC_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📑 Use Same RFC"],
        ["📄 Use Different RFC"],
        ["🏬 Change Warehouse", "⬅️ Back to Main Menu"],
    ],
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
    [
        ["✍️ Try Another RFC"],
        ["🏬 Change Warehouse", "⬅️ Back to Main Menu"],
    ],
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

def get_warehouse_keyboard():
    """Generates a 2-column reply keyboard with all predefined warehouses."""
    buttons = []
    for i in range(0, len(FIXED_WAREHOUSES), 2):
        row = [FIXED_WAREHOUSES[i]]
        if i + 1 < len(FIXED_WAREHOUSES):
            row.append(FIXED_WAREHOUSES[i + 1])
        buttons.append(row)

    buttons.append(["⬅️ Back to Main Menu"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)

# Add this keyboard definition to keyboards.py

TECHNICIAN_RFC_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🏬 Change Warehouse", "⬅️ Back to Main Menu"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)
