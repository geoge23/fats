import logging
import os

logger = logging.getLogger(__name__)
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logger.setLevel(getattr(logging, log_level, logging.INFO))
logger.addHandler(logging.StreamHandler())

log = logger.info
debug = logger.debug
warning = logger.warning
error = logger.error
