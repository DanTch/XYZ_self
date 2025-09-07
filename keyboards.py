from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

def main_menu():
    keyboard = [
        ["👻 سلف 𝐕𝐢𝐩 👻"],
        ["🫠 سلف رایگان 🫠", "🫠 امتیاز رایگان 🫠"],
        ["💍 خرید امتیاز 💍"],
        ["💎 حساب کاربری 💎", "💎 پنل نمایندگی 💎"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def vip_menu():
    keyboard = [
        [InlineKeyboardButton("سلف چیست 🤖 ?", callback_data="what_is_self")],
        [InlineKeyboardButton("خرید سلف vip 🔥", callback_data="buy_vip")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def buy_points_menu():
    keyboard = [
        [InlineKeyboardButton("10 امتیاز (10 تومان)", callback_data="buy_10")],
        [InlineKeyboardButton("25 امتیاز (25 تومان)", callback_data="buy_25")],
        [InlineKeyboardButton("50 امتیاز (45 تومان)", callback_data="buy_50")],
        [InlineKeyboardButton("100 امتیاز (85 تومان)", callback_data="buy_100")],
        [InlineKeyboardButton("250 امتیاز (200 تومان)", callback_data="buy_250")],
        [InlineKeyboardButton("خرید امتیاز دلخواه", callback_data="buy_custom")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_menu():
    keyboard = [
        [InlineKeyboardButton("افزودن امتیاز", callback_data="admin_add_points")],
        [InlineKeyboardButton("گزارش فروش", callback_data="admin_sales_report")],
        [InlineKeyboardButton("کاربران جدید", callback_data="admin_new_users")]
    ]
    return InlineKeyboardMarkup(keyboard)

def reseller_menu():  # تابع جدید
    keyboard = [
        [InlineKeyboardButton("خرید پنل نمایندگی 🔥", callback_data="buy_reseller")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)