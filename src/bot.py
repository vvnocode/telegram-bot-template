#!/usr/bin/env python3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import config
from user_check import check_user_permission
from logger import logger

class VPSChangeIPBot:
    def __init__(self):
        self.app = None
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理/start命令"""

        # 验证用户权限
        if not await check_user_permission(update):
            return
        
        user_id = update.effective_user.id
        user_name = update.effective_user.username
        full_name = update.effective_user.full_name
        logger.info(f"收到 start 命令，用户ID: {user_id}，用户名: {user_name}，全名: {full_name}")
            
        # 回复用户
        await update.message.reply_text(
            text=f"收到 start 命令，用户ID: {user_id}，用户名: {user_name}，全名: {full_name}"
        )

    def run(self):
        """运行机器人"""
        logger.info("机器人开始初始化...")
        self.app = ApplicationBuilder().token(config["telegram_bot_token"]).build()
        
        # 添加命令处理器
        logger.info("注册命令处理器...")
        self.app.add_handler(CommandHandler("start", self.start))

        # 启动机器人
        logger.info("机器人开始运行...")
        self.app.run_polling()
