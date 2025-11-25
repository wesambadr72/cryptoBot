import logging
import sys
from pathlib import Path
def setup_logging(log_file: str, name: str) -> logging.Logger:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True) # تأكد من وجود مجلد logs

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False # منع إرسال السجلات إلى المسجل الجذري الافتراضي

    # إزالة أي معالجات موجودة لتجنب تكرار السجلات
    if logger.hasHandlers():
        logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_dir / log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    # Console handler (لإظهار السجلات في الطرفية أيضًا)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

    return logger

# Usage example (uncomment to test):
# if __name__ != "__main__":
#     # In any other file, simply do:
#     # from utils.logging import get_logger
#     # logger = get_logger(__name__)
#     # logger.info("Your message here")
