#!/usr/bin/env python3

import os
import sys

# 添加项目根目录到Python路径
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.bot.core import TelegramBot
from src.config import load_config
from src.logger import logger

def main():
    """主函数，启动机器人"""
    try:
        # 加载配置
        config = load_config()
        
        # 创建并运行机器人
        logger.info("启动Telegram机器人...")
        bot = TelegramBot(config)
        bot.run()
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号，机器人正在停止...")
    except Exception as e:
        logger.error(f"机器人运行出错: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("机器人已停止")

if __name__ == "__main__":
    main() 