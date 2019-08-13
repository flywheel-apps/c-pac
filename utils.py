"""
This file contains various common utilities that facilitate gear excecution
"""
import logging
import sys
import re

def escape_shell_chars(path):
    """
    Ensure that a path contains all shell-safe characters
    """
    return re.sub('[^0-9a-zA-Z./]+', '_', path)

def get_Custom_Logger(log_name):
    # Initialize Custom Logging
    # Timestamps with logging assist debugging algorithms
    # With long execution times
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(
                fmt='%(levelname)s - %(name)-8s - %(asctime)s -  %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger = logging.getLogger(log_name)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger