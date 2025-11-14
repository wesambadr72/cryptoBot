import logging
# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout), # info/debug/warning
        logging.StreamHandler(sys.stderr)] #error/critical
)
# Create a logger instance for this module so every file can log with its own name
logger = logging.getLogger(__name__)
# Usage example (uncomment to test):
# if __name__ != "__main__":
#     # In any other file, simply do:
#     # from utils.logging import logger
#     # logger.info("Your message here")
