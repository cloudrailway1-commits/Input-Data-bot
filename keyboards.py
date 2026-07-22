from telegram import ReplyKeyboardMarkup

# ==========================================================
# ROLE KEYBOARD
# ==========================================================

ROLE_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🏭 Warehouse Engineer"],
        ["🛠 Technician"],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    is_persistent=True,
    input_field_placeholder="Select your role...",
)

# ==========================================================
# FINISH / RESTART KEYBOARD
# ==========================================================

FINISH_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🔄 New Report"],
        ["❌ Exit"],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    is_persistent=True,
    input_field_placeholder="Choose an option...",
)

# ==========================================================
# YES / NO KEYBOARD
# ==========================================================

YES_NO_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["✅ Yes", "❌ No"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

# ==========================================================
# CANCEL KEYBOARD
# ==========================================================

CANCEL_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["❌ Cancel"],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)

# ==========================================================
# REMOVE KEYBOARD
# ==========================================================

REMOVE_KEYBOARD = ReplyKeyboardMarkup(
    [[]],
    resize_keyboard=True,
)