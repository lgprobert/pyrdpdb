# -*- coding: utf-8 -*-
import logging

"""
logger component, log some userful information for debug

"""


def configure_logging(log_level=logging.ERROR, log_file_name="pyrdp.log"):
    """
    get logger
    :param appName: application name
    :param logFileName: log fiel name
    :return: logger object
    """

    logger = logging.getLogger("pyrdp")
    logger.setLevel(log_level)

    formatter = logging.Formatter("[%(levelname)s: %(name)s] %(message)s")
    # formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s") # noqa

    file_handler = logging.FileHandler(log_file_name)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(log_level)

    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    logging.getLogger().setLevel(logging.WARNING)
    logger.propagate = False

    return logger
