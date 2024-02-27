import logging
from os import environ
from logging.handlers import RotatingFileHandler


def setup_logging_config(name: str, output_file_name: str) -> logging.Logger:
    """Sets up the logging, takes the name of the file and output to write to.

    Args:
        name (str): The __name__ of the file.
        output_file_name (str): Output file name, e.g. heat.log

    Returns:
        logging.Logger: Logger class, which is used to log messages.
    """
    if "PRODUCTION" in environ:
        logging.basicConfig(
            handlers=[
                RotatingFileHandler(
                    filename="/logs/{}".format(output_file_name),
                    mode="w",
                    maxBytes=512000,
                    backupCount=4,
                )
            ],
            level=logging.DEBUG,
            format="%(levelname)s %(asctime)s %(message)s",
            datefmt="%m/%d/%Y%I:%M:%S %p",
        )
    else:
        logging.basicConfig(
            handlers=[
                RotatingFileHandler(
                    filename=output_file_name, mode="w", maxBytes=512000, backupCount=4
                ),
                logging.StreamHandler(),
            ],
            level=logging.DEBUG,
            format="%(levelname)s %(asctime)s %(message)s",
            datefmt="%m/%d/%Y%I:%M:%S %p",
        )

    return logging.getLogger(name)
