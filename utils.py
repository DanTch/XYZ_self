from config import *

def calculate_referral_bonus(user_id, base_points, db_instance):
    """محاسبه پاداش چندلایه برای دعوت‌کنندگان"""
    bonuses = {}
    level1 = get_inviter(user_id, db_instance)
    if level1:
        bonuses[level1] = base_points
        level2 = get_inviter(level1, db_instance)
        if level2:
            bonuses[level2] = base_points // 5  # یک پنجم امتیاز
    return bonuses

def get_inviter(user_id, db_instance):
    """دریافت دعوت‌کننده مستقیم کاربر"""
    user = db_instance.get_user(user_id)
    if user:
        return user[5]  # invited_by
    return None

def format_user_info(user_data, referrals_count):
    """فرمت‌دهی اطلاعات کاربر"""
    return f"""
👤 نام: {user_data[1]} {user_data[2]}
🆔 آیدی: {user_data[0]}
👥 یوزرنیم: @{user_data[3] if user_data[3] else 'ندارد'}
💎 امتیاز: {user_data[4]}
🔗 تعداد دعوت: {referrals_count}
"""