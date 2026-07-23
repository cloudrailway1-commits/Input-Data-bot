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

# Add these at the bottom of keyboards.py

# ==========================================================
# AFTER RFC REGISTER KEYBOARD (WAREHOUSE)
# ==========================================================

AFTER_REGISTER_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["➕ Add More RFC", "⬅️ Back to Main Menu"],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    is_persistent=True,
    input_field_placeholder="Choose an option...",
)

# ==========================================================
# AFTER REPORT KEYBOARD (TECHNICIAN)
# ==========================================================

AFTER_REPORT_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📋 Submit Another Report", "⬅️ Back to Main Menu"],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    is_persistent=True,
    input_field_placeholder="Choose an option...",
)

# ==========================================================
# SAME / DIFFERENT KEYBOARD
# ==========================================================

SAME_DIFFERENT_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🔄 Use Same Name", "✍️ Use Different Name"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

SAME_RFC_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📑 Use Same RFC", "📄 Use Different RFC"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)
# ==========================================================
# NOT FOUND RFC KEYBOARD (TECHNICIAN)
# ==========================================================

RFC_NOT_FOUND_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["✍️ Try Another RFC"],
        ["🔄 Change Name", "⬅️ Back to Main Menu"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


# ==========================================================
# NO RFCS AVAILABLE KEYBOARD
# ==========================================================

NO_RFC_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["⬅️ Back to Main Menu"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


# ==========================================================
# PREVIEW & CONFIRM KEYBOARD
# ==========================================================

PREVIEW_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["✅ Confirm & Submit"],
        ["✏️ Edit Answers", "❌ Cancel Report"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

CANCEL_EDIT_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["❌ Cancel Editing"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)
