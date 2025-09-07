import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, PicklePersistence, filters
from handlers import *
from admin import *
from database import Database

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def main():
    # ایجاد دیتابیس
    db = Database()
    
    # ایجاد updater با persistence
    persistence = PicklePersistence(filename='bot_data')
    updater = Updater(BOT_TOKEN, persistence=persistence)
    dp = updater.dispatcher
    
    # دستورات اصلی
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin_panel))
    dp.add_handler(CommandHandler("add_points", add_points_command, pass_args=True))
    
    # کالبک‌های اصلی
    dp.add_handler(CallbackQueryHandler(vip_handler, pattern='^(what_is_self|buy_vip)$'))
    dp.add_handler(CallbackQueryHandler(buy_points_handler, pattern='^buy_'))
    dp.add_handler(CallbackQueryHandler(admin_confirm_payment, pattern='^(confirm|reject)_'))
    dp.add_handler(CallbackQueryHandler(reseller_handler, pattern='^buy_reseller$'))
    dp.add_handler(CallbackQueryHandler(admin_add_points, pattern='^admin_add_points$'))
    dp.add_handler(CallbackQueryHandler(admin_sales_report, pattern='^admin_sales_report$'))
    dp.add_handler(CallbackQueryHandler(admin_new_users, pattern='^admin_new_users$'))
    dp.add_handler(CallbackQueryHandler(lambda u, c: u.message.reply_text("منوی اصلی:", reply_markup=main_menu()), pattern='^back_to_main$'))
    
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
    dp.add_handler(conv_handler)
    
    # هندلرهای متنی
    dp.add_handler(MessageHandler(filters.Regex('^👻 سلف 𝐕𝐢𝐩 👻$'), vip_handler))
    dp.add_handler(MessageHandler(filters.Regex('^🫠 سلف رایگان 🫠$'), free_self_handler))
    dp.add_handler(MessageHandler(filters.Regex('^🫠 امتیاز رایگان 🫠$'), free_self_handler))
    dp.add_handler(MessageHandler(filters.Regex('^💍 خرید امتیاز 💍$'), buy_points_handler))
    dp.add_handler(MessageHandler(filters.Regex('^💎 حساب کاربری 💎$'), account_handler))
    dp.add_handler(MessageHandler(filters.Regex('^💎 پنل نمایندگی 💎$'), reseller_handler))
    
    # شروع ربات
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()