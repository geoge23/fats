import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

log = logger.info
debug = logger.debug
warning = logger.warning
error = logger.error