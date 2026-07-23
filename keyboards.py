from telegram import ReplyKeyboardMarkup

# Existing keyboards...
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

def get_warehouse_keyboard(warehouses_list: list):
    """Generates a reply keyboard listing unique warehouses."""
    buttons = [[wh] for wh in warehouses_list]
    buttons.append(["⬅️ Back to Main Menu"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)


def get_rfc_keyboard(rfcs_list: list):
    """Generates a reply keyboard listing RFC IDs for a selected warehouse."""
    buttons = [[rfc] for rfc in rfcs_list]
    buttons.append(["⬅️ Back to Main Menu"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
