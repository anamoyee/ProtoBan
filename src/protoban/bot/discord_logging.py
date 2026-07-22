import datetime as dt
from typing import Any

import hikari

from ..data import Data__
from ..get_logger import get_logger
from .settings import S

logger = get_logger(__name__)


async def discord_log(bot: hikari.GatewayBot, content: Any, *, guild_id: hikari.Snowflake) -> None:
	"""Log to the configured logs channel for the given guild.

	Args:
		bot: The Hikari GatewayBot instance.
		content: The message content to log.
		guild_id: The ID of the guild to log to.
	"""

	channel_id = Data__.read_logs_channel(guild_id)

	if channel_id is None:
		return  # noop if channel is not set

	try:
		await bot.rest.create_message(channel_id, content)
	except Exception as e:
		logger.exception(
			"Failed to send log message to channel %(channel_id)r in guild %(guild_id)r",
			{"channel_id": channel_id, "guild_id": guild_id},
			exc_info=(type(e), e, e.__traceback__),
		)


async def discord_log__user_banned_for_leaving(bot: hikari.GatewayBot, *, target: hikari.User, guild_id: hikari.Snowflake) -> None:
	"""Log a successful ban to the configured logs channel for the given guild.

	Args:
		bot: The Hikari GatewayBot instance.
		target: The user who was banned.
		guild_id: The ID of the guild where the ban occurred.
	"""
	await discord_log(
		bot,
		hikari.Embed(
			title="User left & got banned",
			description=f"""
>>> **User**: {target.global_name or target.username}{f"#{target.discriminator}" if hasattr(target, "discriminator") and target.discriminator != "0" else ""} ({target.mention})
**ID**: `{target.id}`
"""[1:-1],
			# discriminator hasattr, because the attr is deprecated and when the discord's migration comes to effect for bots as well, they will remove it and hikari will follow shortly - in which case the intended behaviour of expr evaluting to "" will be replicated until someone notices and removes that piece of code
			timestamp=dt.datetime.now(tz=S.TZ),
			color=0xFF8000,
		),
		guild_id=guild_id,
	)
