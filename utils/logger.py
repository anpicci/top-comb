import logging
import sys
from types import SimpleNamespace

colors = SimpleNamespace(
    grey="\x1b[38;20m",
    yellow="\x1b[33;20m",
    red="\x1b[31;20m",
    bold_red="\x1b[31;1m",
    green="\x1b[32;20m",
    blue="\x1b[34;20m",
    reset="\x1b[0m"
)

class CustomFormatter(logging.Formatter):
    """ Custom class for formatting """

    format = "%(levelname)s: %(message)s [%(asctime)s] "
    FORMATS = {
        logging.DEBUG: colors.grey + format + colors.reset,
        logging.INFO: colors.green + format + colors.reset,
        logging.WARNING: colors.yellow + format + colors.reset,
        logging.ERROR: colors.red + format + colors.reset,
        logging.CRITICAL: colors.bold_red + format + colors.reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get( record.levelno )
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def get_logger( name ) -> logging.Logger:
    """ Returns a logging instance """

    logger = logging.getLogger(name)

    # Trick to avoid double logging
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)  # or INFO in production

        # StreamHandler for console output
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
                CustomFormatter()
        )
        logger.addHandler(handler)
        logger.propagate = False

    return logger


