import logging

from .environment import testmode


def get_logger(name: str) -> logging.Logger:
	"""Return a logger with the specified name, creating it if necessary.

	Args:
		name: The name of the logger to get.

	Returns:
		logging.Logger: The logger with the given name.
	"""
	logger = logging.getLogger(name)

	logger.setLevel(logging.DEBUG if testmode() else logging.INFO)

	return logger
