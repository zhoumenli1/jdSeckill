import os
import logging
import logging.handlers

logger = logging.getLogger()


def set_logger():
    """初始化 ROOT 记录器
    """
    logger.setLevel(logging.INFO)

    log_filename = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'log', 'output.log'
    )

    formatter = logging.Formatter(
        "[ %(levelname)1.1s %(asctime)s %(module)s:%(lineno)d ] %(message)s",
        datefmt="%y%m%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_filename, when="D", interval=1, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


set_logger()

