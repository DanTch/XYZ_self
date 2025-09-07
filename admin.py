import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, PicklePersistence, filters
from handlers import *
from admin import *
from database import Database

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    chat_id = user.id
    
    # بررسی لینک دعوت
    invited_by = None
    if context.args:
        try:
            invited_by = int(context.args[0])
        except ValueError:
            pass
    
    # افزودن کاربر به دیتابیس
    is_new = db.add_user(
        chat_id,
        user.first_name,
        user.last_name,
        user.username,
        invited_by
    )
    
    if is_new:
        # ارسال نوتیفیکیشن به ادمین
        user_details = f"🍔 کاربر جدید {chat_id} به ربات اضافه شد.\n\n"
        user_details += f"ایدی عددی کاربر: {chat_id}\n"
        user_details += f"نام: {user.first_name if user.first_name else 'نامشخص'}\n"
        user_details += f"نام خانوادگی: {user.last_name if user.last_name else 'نامشخص'}\n"
        
        if user.username:
            user_details += f"یوزرنیم: @{user.username}"
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Go to chat", url=f"https://t.me/{user.username}"))
            await context.bot.send_message(ADMIN_ID, user_details, reply_markup=markup)
        else:
            user_details += f"🔥 User ID: [{user.id}](tg://user?id={user.id})"
            await context.bot.send_message(ADMIN_ID, user_details, parse_mode='Markdown', disable_web_page_preview=True)
        
        # ارسال پیام به دعوت‌کننده
        if invited_by:
            inviter = db.get_user(invited_by)
            if inviter:
                await context.bot.send_message(
                    invited_by,
                    f"کاربری که با کد دعوت شما وارد ربات شده بود، اقدام به عضویت کرد.\n\n"
                    f"🎁 3 امتیاز به شما اضافه شد.\n"
                    f"موجودی جدید: {inviter[4] + REFERRAL_BONUS}"
                )
    
    # ارسال پیام خوشامدگویی
    with open(WELCOME_IMAGE_PATH, 'rb') as photo:
        await update.message.reply_photo(
            photo,
            caption=f"به ربات XYZ سلف خوش آمدید\n\n"
                   f"برای کار کردن با ربات از دستورات زیر استفاده کنید\n\n"
                   f"Dev : @Danyal_net",
            reply_markup=main_menu()
        )

async def main():
    # ایجاد دیتابیس
    db = Database()
    
    # ایجاد application با persistence
    persistence = PicklePersistence(filename='bot_data')
    app = Application.builder().token(BOT_TOKEN).persistence(persistence).build()
    
    # دستورات اصلی
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("add_points", add_points_command, pass_args=True))
    
    # کالبک‌های اصلی
    app.add_handler(CallbackQueryHandler(vip_handler, pattern='^(what_is_self|buy_vip)$'))
    app.add_handler(CallbackQueryHandler(buy_points_handler, pattern='^buy_'))
    app.add_handler(CallbackQueryHandler(admin_confirm_payment, pattern='^(confirm|reject)_'))
    app.add_handler(CallbackQueryHandler(reseller_handler, pattern='^buy_reseller$'))
    app.add_handler(CallbackQueryHandler(admin_add_points, pattern='^admin_add_points$'))
    app.add_handler(CallbackQueryHandler(admin_sales_report, pattern='^admin_sales_report$'))
    app.add_handler(CallbackQueryHandler(admin_new_users, pattern='^admin_new_users$'))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.message.reply_text("منوی اصلی:", reply_markup=main_menu()), pattern='^back_to_main$'))
    
    # هندلرهای مکالمه
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(buy_points_handler, pattern='^buy_points$'),
            CallbackQueryHandler(reseller_handler, pattern='^buy_reseller$')
        ],
        states={
            SELECTING_POINTS: [CallbackQueryHandler(buy_points_handler, pattern='^buy_')],
            AWAITING_PAYMENT: [MessageHandler(filters.PHOTO, payment_received)],
            AWAITING_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, token_received)],
            CUSTOM_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_points_handler)]
        },
        fallbacks=[CommandHandler('cancel', cancel_handler)]
    )
    app.add_handler(conv_handler)
    
    # هندلرهای متنی
    app.add_handler(MessageHandler(filters.Regex('^👻 سلف 𝐕𝐢𝐩 👻$'), vip_handler))
    app.add_handler(MessageHandler(filters.Regex('^🫠 سلف رایگان 🫠$'), free_self_handler))
    app.add_handler(MessageHandler(filters.Regex('^🫠 امتیاز رایگان 🫠$'), free_self_handler))
    app.add_handler(MessageHandler(filters.Regex('^💍 خرید امتیاز 💍$'), buy_points_handler))
    app.add_handler(MessageHandler(filters.Regex('^💎 حساب کاربری 💎$'), account_handler))
    app.add_handler(MessageHandler(filters.Regex('^💎 پنل نمایندگی 💎$'), reseller_handler))
    
    # شروع ربات
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())