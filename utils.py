"""
This file contains various common utilities that facilitate gear excecution
"""
import logging

def escape_shell_chars(path):
    special_chars = [' ', '\t', '\n', '!', '"', '#', '$', '&', '\'', ')']
    special_chars.extend(['(', '*', ',', ';', '<', '=', '>', '?', '[', '\\'])
    special_chars.extend([']', '^', '`', '{', '}', '|', '~', '-', ':'])
    for ch in special_chars:
        path = path.replace(ch,'_')
    return path

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