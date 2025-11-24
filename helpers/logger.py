import logging
import requests

from settings import settings

logger = logging.getLogger()
logger.setLevel(logging.INFO)

for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# formating
format_text = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(format_text)
logger.addHandler(console_handler)

# send log to telegram
def send_log(level, message):
    if not settings.TELEGRAM_TOKEN or not settings.TELEGRAM_IDS:
        return
    
    try:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendMessage"
        
        for chat_id in settings.TELEGRAM_IDS:
            requests.post(url, data={
                'chat_id': chat_id,
                'text': f"#maxBot\n{level}\n{message}"
            }, timeout=5)
    except Exception as e:
        print(e)
        pass

# filter logs
class TelegramLog(logging.Filter):
    def filter(self, record):
        if record.levelno >= logging.WARNING:
            if record.levelno >= logging.ERROR:
                send_log("Ошибка:\n", record.getMessage())
            else:
                send_log("Предупреждение:\n", record.getMessage())
        return True

telegram_filter = TelegramLog()
logger.addFilter(telegram_filter)


# export log
def get_logger():
    return logger