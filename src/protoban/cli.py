import logging
import os
import sys

import arguably
import hikari.internal.ux
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as rich_traceback_install

from ._version import __version__
from .data import Data__
from .get_logger import get_logger


def get_terminal_width() -> int:
	"""Get the width of the terminal, if terminal not found, return 100.

	Returns:
		width: The width of the terminal, or 100 if the terminal is not found.
	"""
	try:
		return os.get_terminal_size().columns
	except OSError:
		return 100


def setup_disable_ctrl_c_printed_on_linux_or_macos_terminals():
	"""Disables ^C echoing while running, then restores settings when exiting."""
	if sys.platform == "win32":
		return

	import atexit

	try:
		import termios

		fd = sys.stdin.fileno()

		# Save original attributes
		original_attrs = termios.tcgetattr(fd)

		# Disable ECHOCTL flag
		new_attrs = termios.tcgetattr(fd)
		new_attrs[3] &= ~termios.ECHOCTL
		termios.tcsetattr(fd, termios.TCSANOW, new_attrs)

		# Register restoration on program shutdown (normal exit or exception)
		def restore():
			termios.tcsetattr(fd, termios.TCSANOW, original_attrs)

		atexit.register(restore)

	except Exception:
		pass  # Ignores errors, this is not critical.


def setup_logging_to_stdout_rich() -> None:
	class RichHandlerForceNoHighlight(RichHandler):
		# NOTE: required because of some unknown unstoppable force-sets the per-log override (kinda like: extra={"highligher": Default::default()}), for any log record which doesnt explicitly set it to None with the previously mentioned extras. So the `self.highligher` argument seems to be entirely useless.
		# NOTE: required because of some unknown unstoppable force-sets the per-log override (kinda like: extra={"highligher": Default::default()}), for any log record which doesnt explicitly set it to None with the previously mentioned extras. So the `self.highligher` argument seems to be entirely useless.
		# NOTE: required because of some unknown unstoppable force-sets the per-log override (kinda like: extra={"highligher": Default::default()}), for any log record which doesnt explicitly set it to None with the previously mentioned extras. So the `self.highligher` argument seems to be entirely useless.
		def emit(self, record: logging.LogRecord) -> None:
			record.highlighter = None
			super().emit(record)

	logging.basicConfig(
		level="INFO",
		format="[b]%(name)s:[/b] %(message)s",  # rich handler does the formatting.
		datefmt="[%H:%M:%S]",
		handlers=[
			RichHandlerForceNoHighlight(
				console=Console(
					highlight=False,
					highlighter=None,
					tab_size=4,
				),
				rich_tracebacks=True,
				tracebacks_show_locals=False,
				markup=True,
				highlighter=None,
			)
		],
	)


def setup_logging_to_file() -> None:
	root_logger = logging.getLogger()

	file_handler = logging.FileHandler(Data__.LOG_CURRENT, mode="a", encoding="utf-8")

	file_handler.setFormatter(
		formatter := logging.Formatter(
			fmt="%(levelname).1s %(asctime)s %(name)s: %(message)s",
			datefmt="%Y-%m-%d %H:%M:%S",  # tried to add miliseconds, but logging apparently poorly supports them...
		)
	)

	root_logger.addHandler(file_handler)


def run() -> None:
	from .bot import BOT

	BOT.run()


@arguably.command
def __root__(
	*,
	debug_print_token: bool = False,
):
	"""Run the app.

	Args:
		debug_print_token: Print the token to stdout and exit. Useful when it says unexpected token format but you think your token is correct.
	"""

	setup_disable_ctrl_c_printed_on_linux_or_macos_terminals()  # contains its own `atexit` restoration

	rich_traceback_install(
		width=get_terminal_width(),
	)

	if os.environ.get("BOT_TOKEN", None) is None:
		print("BOT_TOKEN environment variable is required.")
		sys.exit(1)

	os.environ["BOT_TOKEN"] = os.environ["BOT_TOKEN"].strip()

	if debug_print_token:
		print(f"token={os.environ["BOT_TOKEN"]!r}")
		sys.exit(2)

	if os.environ.get("BOT_ENVIRONMENT", None) is None:
		os.environ["BOT_ENVIRONMENT"] = "prod"

	setup_logging_to_stdout_rich()

	hikari.internal.ux.print_banner("hikari", allow_color=True, force_color=False)
	logger = get_logger(__name__)

	if True:  # "pre-starting event"
		if Data__.LOG_CURRENT.exists():
			logger.warning("Unrotated current log file exists (probably from a previous run that might have exited unexpectedly). Rotating it now...")
			new_path = Data__.rotate_current_log()
			logger.info("Rotated current log file to: %s", new_path)

		setup_logging_to_file()

	try:
		run()
	except (ValueError,)[0] as e:  # tuple tricks to shut up ruff docstring requirement...
		if str(e) == "Unexpected token format":
			e.add_note("See the provided contents of token with --debug-print-token")

		raise

	if True:  # "post-stopped event"
		if Data__.LOG_CURRENT.exists():
			new_path = Data__.rotate_current_log()
			logger.info("Rotated current log file to: %s", new_path)
			Data__.LOG_CURRENT.unlink(missing_ok=True)
		else:
			logger.warning("Current log file does not exist...? Cannot rotate a missing file.")


def main():
	sys.modules["__main__"].__version__ = __version__  # arguably version fix  # ty:ignore[unresolved-attribute]
	arguably.run(
		version_flag=("-V", "--version"),
	)
