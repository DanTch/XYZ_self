from config import *

def calculate_referral_bonus(user_id, base_points):
    """محاسبه پاداش چندلایه برای دعوت‌کنندگان"""
    bonuses = {}
    level1 = get_inviter(user_id)
    if level1:
        bonuses[level1] = base_points
        level2 = get_inviter(level1)
        if level2:
            bonuses[level2] = base_points // 5  # یک پنجم امتیاز
    return bonuses

def get_inviter(user_id):
    """دریافت دعوت‌کننده مستقیم کاربر"""
    # این تابع باید در database.py پیاده‌سازی شود
    pass

def format_user_info(user_data):
    """فرمت‌دهی اطلاعات کاربر"""
    return f"""
👤 نام: {user_data[1]} {user_data[2]}
🆔 آیدی: {user_data[0]}
👥 یوزرنیم: @{user_data[3] if user_data[3] else 'ندارد'}
💎 امتیاز: {user_data[4]}
🔗 تعداد دعوت: {len(get_referrals(user_data[0]))}
"""