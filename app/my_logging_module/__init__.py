# __init__.py
import logging

def setup_logging(logger_name='sane_logger'):
    """Set up logging with a named logger."""
    # Create or get a logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Create a formatter
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")

    # fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, fileName))
    # fileHandler.setFormatter(logFormatter)
    # logger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)

    return logger

# Automatically create a logger named 'sane_logger'
sane_logger = setup_logging('sane_logger')
