import os
from enum import StrEnum

from ._version import __version__


class Environment(StrEnum):
	DEV = "dev"
	PROD = "prod"


def get_environment() -> Environment:
	try:
		env = Environment(os.environ.get("BOT_ENVIRONMENT", "prod"))
	except ValueError as e:
		note = f"BOT_ENVIRONMENT environment variable must be set to either of: {", ".join(f"{e.value!r}" for e in Environment)}, got: {os.environ.get("BOT_ENVIRONMENT")!r}"
		e.add_note(note)
		raise

	return env


def testmode() -> str:
	"""Return '' if not in testmode, else return f' - v{__version__}'."""
	return f" (Testmode, v{__version__})" if get_environment() == Environment.DEV else ""
