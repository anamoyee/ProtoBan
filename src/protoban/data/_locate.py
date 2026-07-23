import itertools as it
import pathlib as p

import hikari
import platformdirs
from nya_scope import Scope

from ..environment import get_environment


class Data__(Scope):
	"""Theese paths do not necessarily point to files that exist, except for assets. Ensure existance by creating if missing."""

	@staticmethod
	def ROOT() -> p.Path:
		if __package__ is None:
			msg = "__package__ is None, expected this app to be packaged, do not run the app as script."
			raise AssertionError(msg)  # not using assert because i want this to keep being raised even in -OO

		# path = p.Path(__file__).parent.resolve()
		path = p.Path(platformdirs.user_data_dir(__package__.split(".", maxsplit=1)[0], appauthor=False, roaming=False)) / get_environment().value
		path.mkdir(parents=True, exist_ok=True)
		return path

	class Assets__(Scope):
		"""Assets that are bundled with the bot (not .gitignore)."""

		@staticmethod
		def ROOT() -> p.Path:
			return p.Path(__file__).parent.resolve() / "assets"
			# asserts are free of the data platformdirs/gitdir schenanigans, always in the gitdir.

		@staticmethod
		def MEGU_BUTTON() -> p.Path:
			return Data__.Assets__.ROOT() / "megu_button.png"

	if True:  # ban reason

		@staticmethod
		def BAN_REASON_DIR() -> p.Path:
			path = Data__.ROOT() / "ban_reason"
			path.mkdir(exist_ok=True)
			return path

		@classmethod
		def read_ban_reason(cls, guild_id: hikari.Snowflake) -> str:
			"""Read the ban reason from the file, or return a default reason if the file does not exist.

			Args:
				guild_id (hikari.Snowflake): The ID of the guild for which to read the ban reason.

			Returns:
				str: The ban reason read from the file, or a default reason if the file does not exist.
			"""
			file = cls.BAN_REASON_DIR() / f"{guild_id}"

			if file.exists():
				return file.read_text(encoding="utf-8")

			return f"({__package__}: reason field unconfigured)"

		@classmethod
		def write_ban_reason(cls, *, guild_id: hikari.Snowflake, new_reason: str) -> int:
			"""Write the ban reason to the file.

			Args:
				guild_id (hikari.Snowflake): The ID of the guild for which to write the ban reason.
				new_reason (str): The ban reason to write to the file.

			Returns:
				int: The number of characters written to the file.
			"""
			file = cls.BAN_REASON_DIR() / f"{guild_id}"

			return file.write_text(new_reason, encoding="utf-8")

		@classmethod
		def unlink_ban_reason(cls, guild_id: hikari.Snowflake) -> None:
			"""Unset the ban reason by deleting the file.

			Args:
				guild_id (hikari.Snowflake): The ID of the guild for which to unset the ban reason.

			Raises:
				FileNotFoundError: If the file does not exist.
			"""
			file = cls.BAN_REASON_DIR() / f"{guild_id}"

			if not file.exists():
				msg = f"Cannot unset ban reason for guild {guild_id}, file does not exist: {file}"
				raise FileNotFoundError(msg)

			file.unlink()

	if True:  # file logs

		@staticmethod
		def LOG_CURRENT() -> p.Path:
			path = Data__.ROOT() / "logs/current.log"
			path.parent.mkdir(parents=True, exist_ok=True)
			return path

		@staticmethod
		def LOG_ARCHIVE_DIR() -> p.Path:
			path = Data__.ROOT() / "logs/archive"
			path.mkdir(parents=True, exist_ok=True)
			return path

		@classmethod
		def rotate_current_log(cls) -> p.Path:
			"""Rotate the current log file to the archive logs directory. Does not create a new current log file.

			Returns:
				p.Path: The new path of the rotated log file (e.g. `logs/archive/log_1.log` - relative to the data root).

			Raises:
				FileNotFoundError: If the current log file does not exist.
			"""

			def find_next_available_archive_logs_path(prefix: str = "log_") -> p.Path:
				for i in it.count(1):
					new_name = cls.LOG_ARCHIVE_DIR() / f"{prefix}{i}.log"
					if not new_name.exists():
						new_name.parent.mkdir(parents=True, exist_ok=True)
						return new_name

				# there to appease the typecheckers
				msg_0 = "Unreachable: itertools.count() should never stop yielding and only way to exit the loop is to return."
				raise RuntimeError(msg_0)

			if not cls.LOG_CURRENT().exists():
				msg_1 = f"Current log file does not exist: {cls.LOG_CURRENT()}"
				raise FileNotFoundError(msg_1)

			new_path = find_next_available_archive_logs_path()
			cls.LOG_CURRENT().rename(new_path)
			return new_path.relative_to(cls.ROOT())

	if True:  # discord logs

		@staticmethod
		def DISCORD_LOGS_CHANNEL_DIR() -> p.Path:
			path = Data__.ROOT() / "logs_channel"
			path.mkdir(parents=True, exist_ok=True)
			return path

		@classmethod
		def read_logs_channel(cls, guild_id: hikari.Snowflake) -> hikari.Snowflake | None:
			"""Read the logs channel ID from the file, or return None if the file does not exist.

			Args:
				guild_id (hikari.Snowflake): The ID of the guild for which to read the logs channel ID.

			Returns:
				hikari.Snowflake | None: The logs channel ID read from the file, or None if the file does not exist.

			Raises:
				ValueError: If the logs channel ID in the file is malformed (not an int-parsable string). This indicates a bug with the code, as this should never be possible.
			"""
			file = cls.DISCORD_LOGS_CHANNEL_DIR() / f"{guild_id}"

			if not file.exists():
				return None

			snowflake_str = file.read_text(encoding="utf-8").strip()

			try:
				return hikari.Snowflake(snowflake_str)
			except ValueError as e:
				msg = f"Malformed logs channel ID {snowflake_str[:50]!r} in file {file}, expected int-parsable string. This indicates a bug with the code, as this should never be possible, therefore raising."
				raise ValueError(msg) from e

		@classmethod
		def write_logs_channel(cls, *, guild_id: hikari.Snowflake, new_channel_id: hikari.Snowflake) -> int:
			"""Write the logs channel ID to the file.

			Args:
				guild_id (hikari.Snowflake): The ID of the guild for which to write the logs channel ID.
				new_channel_id (hikari.Snowflake): The logs channel ID to write to the file.

			Returns:
				int: The number of characters written to the file.
			"""
			file = cls.DISCORD_LOGS_CHANNEL_DIR() / f"{guild_id}"

			return file.write_text(str(new_channel_id), encoding="utf-8")

		@classmethod
		def unlink_logs_channel(cls, guild_id: hikari.Snowflake) -> None:
			"""Unset the logs channel ID by deleting the file.

			Args:
				guild_id (hikari.Snowflake): The ID of the guild for which to unset the logs channel ID.

			Raises:
				FileNotFoundError: If the file does not exist.
			"""
			file = cls.DISCORD_LOGS_CHANNEL_DIR() / f"{guild_id}"

			if not file.exists():
				msg = f"Cannot unset logs channel ID for guild {guild_id}, file does not exist: {file}"
				raise FileNotFoundError(msg)

			file.unlink()

	if True:  # banned_users

		@staticmethod
		def BANNED_USERS_DIR() -> p.Path:
			path = Data__.ROOT() / "banned_users"
			path.mkdir(parents=True, exist_ok=True)
			return path

		@classmethod
		def read_banned_users(cls, guild_id: hikari.Snowflake) -> dict[hikari.Snowflake, tuple[str, str]]:
			"""Read the banned users from the file, or return an empty set if the file does not exist.

			Args:
				guild_id: The ID of the guild for which to read the banned users.

			Returns:
				dict[hikari.Snowflake, tuple[str, str]]: The dictionary mapping banned user IDs to their usernames and reasons at time of ban.

			Raises:
				RuntimeError: If a non-file is found in the banned users directory. This indicates a bug with the code, as this should never be possible.
				RuntimeError: If a malformed user ID is found in the file name of the banned users directory. This indicates a bug with the code
			"""
			directory = cls.BANNED_USERS_DIR() / f"{guild_id}"
			directory.mkdir(exist_ok=True)
			dct: dict[hikari.Snowflake, tuple[str, str]] = {}

			for file in sorted(directory.iterdir(), key=lambda f: f.stat().st_mtime):
				if not file.is_file():
					msg = f"Found non-file in banned users directory {file}, expected only files. This indicates a bug with the code, as this should never be possible, therefore raising."
					raise RuntimeError(msg)

				try:
					snowflake = hikari.Snowflake(file.name)
				except ValueError as e:
					msg = f"Malformed user ID {file.name!r} in file name of {file}, expected int-parsable string. This indicates a bug with the code, as this should never be possible, therefore raising."
					raise RuntimeError(msg) from e

				username, reason = file.read_text(encoding="utf-8").split("\n", maxsplit=1)

				dct[snowflake] = (username, reason)

			return dct

		@classmethod
		def read_banned_user(cls, *, guild_id: hikari.Snowflake, user_id: hikari.Snowflake) -> tuple[str, str] | None:
			"""Read a banned user from the file, or return None if the file does not exist.

			Args:
				guild_id: The ID of the guild for which to read the banned user.
				user_id: The ID of the user to read.

			Returns:
				tuple[str, str] | None: The username and reason for the banned user, or None if the user is not banned.
			"""
			directory = cls.BANNED_USERS_DIR() / f"{guild_id}"
			directory.mkdir(exist_ok=True)
			file = directory / f"{user_id}"

			if not file.is_file():
				return None

			username, reason = file.read_text(encoding="utf-8").split("\n", maxsplit=1)
			return username, reason

		@classmethod
		def add_banned_user(cls, *, guild_id: hikari.Snowflake, user_id: hikari.Snowflake, username: str, reason: str) -> None:
			"""Add a banned user by creating a file with the user ID as the name.

			Args:
				guild_id: The ID of the guild for which to add the banned user.
				user_id: The ID of the user to add as banned.
				username: The username of the user to add as banned.
				reason: The reason for banning the user.
			"""
			directory = cls.BANNED_USERS_DIR() / f"{guild_id}"
			directory.mkdir(exist_ok=True)

			file = directory / f"{user_id}"

			file.touch(exist_ok=True)
			file.write_text(f"{username}\n{reason}", encoding="utf-8")

		@classmethod
		def remove_banned_user(cls, *, guild_id: hikari.Snowflake, user_id: hikari.Snowflake) -> None:
			"""Remove a banned user by deleting the file with the user ID as the name.

			Args:
				guild_id: The ID of the guild for which to remove the banned user.
				user_id: The ID of the user to remove from banned.
			"""
			directory = cls.BANNED_USERS_DIR() / f"{guild_id}"
			directory.mkdir(exist_ok=True)

			file = directory / f"{user_id}"

			file.unlink(missing_ok=True)


(Data__.ROOT() / ".gitignore").write_text(
	"""
*
!*.py
!.gitignore
!assets/
"""[1:]
)
