"""消息处理辅助工具"""
from typing import Optional, Dict, Any, List

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from src.logger import logger


class MessageHelper:
    """消息处理辅助工具类"""
    
    @staticmethod
    async def reply_with_markdown(
        update: Update, 
        text: str, 
        reply_markup: Optional[InlineKeyboardMarkup] = None
    ) -> None:
        """使用Markdown格式回复消息
        
        Args:
            update: Telegram更新对象
            text: 回复内容
            reply_markup: 内联键盘标记
        """
        try:
            await update.message.reply_text(
                text=text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"回复消息出错: {str(e)}")
            # 尝试不使用Markdown格式重新发送
            try:
                await update.message.reply_text(
                    text="消息发送出错，可能包含不兼容的格式。请查看日志获取详情。",
                    reply_markup=reply_markup
                )
            except Exception as e2:
                logger.error(f"重试回复消息也出错: {str(e2)}")
    
    @staticmethod
    def create_button_grid(
        buttons: List[Dict[str, str]], 
        columns: int = 2
    ) -> InlineKeyboardMarkup:
        """创建按钮网格
        
        Args:
            buttons: 按钮列表，每个按钮是一个字典，包含text和callback_data
            columns: 每行按钮数量
            
        Returns:
            网格布局的内联键盘标记
        """
        keyboard = []
        row = []
        
        for i, button in enumerate(buttons):
            row.append(InlineKeyboardButton(
                text=button['text'],
                callback_data=button['callback_data']
            ))
            
            # 当一行已满或已是最后一个按钮时，添加行到键盘
            if (i + 1) % columns == 0 or i == len(buttons) - 1:
                keyboard.append(row)
                row = []
                
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    async def edit_message_text(
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None
    ) -> bool:
        """编辑现有消息文本
        
        Args:
            update: Telegram更新对象
            context: 上下文对象
            text: 新文本
            reply_markup: 新的内联键盘标记
            
        Returns:
            编辑成功与否
        """
        query = update.callback_query
        
        try:
            await query.edit_message_text(
                text=text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return True
        except Exception as e:
            logger.error(f"编辑消息出错: {str(e)}")
            try:
                await query.edit_message_text(
                    text="消息编辑出错，可能包含不兼容的格式。",
                    reply_markup=reply_markup
                )
            except Exception as e2:
                logger.error(f"重试编辑消息也出错: {str(e2)}")
            return False 