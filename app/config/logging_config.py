import logging
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
# logger = logging.getLogger("uvicorn")
logger = logging.getLogger(__name__)
