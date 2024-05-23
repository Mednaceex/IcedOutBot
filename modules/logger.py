import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

log_name = Path('logs', 'bot_logs.log')
logging.getLogger('discord.app_commands.tree').setLevel(logging.CRITICAL)
logger = logging.getLogger(__name__)
handler = TimedRotatingFileHandler(log_name, when="midnight", interval=1, backupCount=30, encoding=None, delay=False,
                                   utc=True, atTime=datetime(2023, 8, 16, 9))
handler.suffix = "%d_%m_%Y"
fmt = logging.Formatter(fmt='%(asctime)s: %(name)s: %(levelname)s: %(message)s', datefmt='%d.%m.%Y %H:%M:%S')
logger.setLevel(logging.DEBUG)
handler.setLevel(logging.DEBUG)
handler.setFormatter(fmt)
logger.addHandler(handler)


def log_errors(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(repr(e))

    return wrapper
