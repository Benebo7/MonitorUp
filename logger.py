import logging
from pythonjsonlogger import jsonlogger
import os
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("fastapi_app")
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
if os.getenv("ENVIRONMENT") == "DEV":
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)