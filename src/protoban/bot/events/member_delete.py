import datetime as dt
from collections.abc import AsyncGenerator

import hikari
from asyncstdlib import enumerate as aenumerate
from nya_fmt import Formatter as Fmt

from ...data import Data__
from ...get_logger import get_logger
from ..bot import BOT
from ..discord_logging import discord_log__user_banned_for_leaving
from ..settings import S

logger = get_logger(__name__)

fmt = Fmt()


async def flatten_audit_log_entries(
	audit_log_aiterator: hikari.iterators.LazyIterator[hikari.AuditLog],
) -> AsyncGenerator[tuple[hikari.Snowflake, hikari.AuditLogEntry]]:
	"""Flatten an audit log aiterator into a list of entries.

	Args:
		audit_log_aiterator: The audit log aiterator to flatten.

	Yields:
		tuple[hikari.Snowflake, hikari.AuditLogEntry]: A tuple of the entry's target user ID and the entry itself.
	"""
	async for page in audit_log_aiterator:
		for snowflake, entry in page.entries.items():
			yield snowflake, entry


def is_audit_log_entry_recent_enough(entry: hikari.AuditLogEntry, max_age_seconds: dt.timedelta = dt.timedelta(seconds=5)) -> bool:
	"""Check if an audit log entry is recent enough.

	Args:
		entry: The audit log entry to check.
		max_age_seconds: The maximum age of the entry in seconds.

	Returns:
		bool: True if the entry is recent enough, False otherwise.
	"""
	entry_age = (dt.datetime.now(tz=S.TZ)) - entry.created_at
	return entry_age <= max_age_seconds


@BOT.listen(hikari.MemberDeleteEvent)
async def on_member_delete(ev: hikari.MemberDeleteEvent) -> None:
	guild = await BOT.rest.fetch_guild(ev.guild_id)

	entry_inspection_limit = 10

	logger.debug("*** User %d left, looking through audit log for ban/kick entries", ev.user_id)
	async for i, (_, entry) in aenumerate(
		flatten_audit_log_entries(
			BOT.rest.fetch_audit_log(
				ev.guild_id,
				# action_type=..., # Do not filter by action type, it does not support mutliple action types, it's not a flag enum.
				# user=..., # Do not filter by user, as this filter's by the administrator user and not the one who's being potentially kicked/banned.
			),
		)
	):
		if i >= entry_inspection_limit:
			logger.debug("❌ Reached entry inspection limit, stopping search for ban/kick entries, assuming no exonerating entry exists.")
			break

		logger.debug("--- entry %d ---", i)
		logger.debug("Found ban/kick entry: %s (created at %s)", fmt(entry), fmt(entry.created_at))

		if entry.action_type not in {
			hikari.AuditLogEventType.MEMBER_BAN_ADD,
			hikari.AuditLogEventType.MEMBER_KICK,
		}:
			logger.debug("❌ Discarding entry %d, action type not relevant", entry.id)
			continue

		if not is_audit_log_entry_recent_enough(entry):
			logger.debug("❌ Discarding entry %d, too old (and breaking out of the loop, since entries are in order)", entry.id)
			break

		if not entry.target_id or entry.target_id != ev.user_id:
			logger.debug("❌ Discarding entry %d, target not relevant", entry.id)
			continue

		logger.debug("Found a convincing ban/kick audit for them to be spared.")  # i meaaan.. if it's ban, they're kicked anyway 💀

		logger.info("User %d left, but was banned/kicked by an administrator manually, not auto-banning them.", ev.user_id)
		return  # user was banned/kicked by an administrator manually, do not auto-ban them then.

	logger.debug("No ban/kick audit log entry found for user %d, proceeding to auto-banning them.", ev.user_id)

	reason = Data__.read_ban_reason(ev.guild_id)
	await guild.ban(ev.user_id, reason=reason)
	Data__.add_banned_user(
		guild_id=ev.guild_id,
		user_id=ev.user_id,
		username=ev.user.username,
		reason=reason,
	)

	logger.info("🔨 Banned user %d from guild %d for leaving the server.", ev.user_id, ev.guild_id)

	await discord_log__user_banned_for_leaving(bot=BOT, target=ev.old_member or ev.user, guild_id=ev.guild_id)
