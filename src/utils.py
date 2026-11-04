import logging
from logging import Logger
import os
import json
import urllib.parse

from src import constants


def init__logger(file_name: str,
                 log_format: str = None,
                 mode: str = "w",
                 debug_level: bool = False) -> Logger:
    """
    """
    if log_format is None:
        log_format = ("%(asctime)s | %(levelname)-7s [%(worker_id)s] %(funcName)s#L-%(lineno)d"
                      " | %(message)s")

    logger = logging.getLogger(file_name)
    if debug_level:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(join_names(file_name), mode=mode)
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger


def adapter_log(base_logger, worket_id: dict):
    return logging.LoggerAdapter(base_logger, worket_id)


def join_names(names: str | list):
    if isinstance(names, str):
        return os.path.join(constants.BASE_DIR, names)
    if isinstance(names, list):
        assert names != [], "<name_list> IS []"
        return os.path.join(constants.BASE_DIR, *names)
    raise TypeError(f"Got a {type(names)}")


def save_json(file_path: str, data: dict | list) -> str:
    """
    """
    json_str = json.dumps(data, ensure_ascii=False, indent=4)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(json_str)
    return file_path


def get_parameter_from_url(url, parameter_name):
    for key_value in urllib.parse.urlparse(url).query.split("&"):
        parts = key_value.split("=")
        if parameter_name != parts[0]:
            continue
        if len(parts) == 1:
            return None
        else:
            return parts[1]
