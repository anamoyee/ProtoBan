import datetime as dt
from collections.abc import Iterable
from datetime import timedelta as Δ
from typing import AsyncGenerator

import arc
import hikari
import nya_fmt
import toolbox
from hikari.permissions import Permissions as P

from ...environment import testmode
from ...get_logger import get_logger
from ..bot import BOT
from ..settings import S

logger = get_logger(__name__)


async def member_has_bypassing_permissions(member: hikari.Member) -> bool:
	"""Return `True` if this member bypasses the inactivity check due to their role permissions."""

	return bool(
		toolbox.calculate_permissions(member)
		& (
			P.ADMINISTRATOR  #
			| P.MANAGE_GUILD
			| P.MANAGE_CHANNELS
			| P.MANAGE_ROLES
			| P.MANAGE_MESSAGES
			| P.BAN_MEMBERS
			| P.KICK_MEMBERS
		)
	)


async def was_member_active_in_channels_after(member: hikari.Member, textable_channels: Iterable[hikari.TextableChannel], after: dt.datetime) -> bool:
	for textable_channel in textable_channels:
		logger.debug("*** *** *** Channel: %d", textable_channel.id)
		async for message in textable_channel.fetch_history(after=after):
			logger.debug("*** *** *** *** Message: %d", message.id)
			if message.author.id == member.id:
				return True
	return False


async def fetch_inactive_members_of_own_guild(
	own_guild: hikari.OwnGuild,
	*,
	after: dt.datetime,
) -> AsyncGenerator[hikari.Member]:
	guild_members = await BOT.rest.fetch_members(own_guild)

	# todo: does not check for activity in channels like media, threads, etc.
	guild_text_channels = (
		ch  #
		for ch in await BOT.rest.fetch_guild_channels(own_guild)
		if isinstance(ch, hikari.TextableGuildChannel)
	)

	BOT.cache.get_guild_channels_view()

	guild: hikari.Guild = BOT.cache.get_guild(own_guild) or await BOT.rest.fetch_guild(own_guild)

	for member in guild_members:
		logger.debug("*** *** Member: %d", member.id)
		if member.is_bot or member.is_system:
			continue

		if guild.owner_id == member.id:
			continue

		if await member_has_bypassing_permissions(member):
			continue

		if await was_member_active_in_channels_after(
			member,
			textable_channels=guild_text_channels,
			after=after,
		):
			continue

		yield member


async def fetch_inactive_members_of_own_guilds(
	own_guilds: hikari.LazyIterator[hikari.OwnGuild],
	*,
	after: dt.datetime,
) -> dict[hikari.OwnGuild, set[hikari.Member]]:
	"""Return a dict of guilds and their inactive members."""
	inactive_members: dict[hikari.OwnGuild, set[hikari.Member]] = {}

	async for own_guild in own_guilds:
		logger.debug("*** Guild: %d", own_guild.id)
		if inactive_members_of_guild := {member async for member in fetch_inactive_members_of_own_guild(own_guild, after=after)}:
			inactive_members[own_guild] = inactive_members_of_guild

	return inactive_members


@arc.utils.interval_loop(
	seconds=(60 * 60),  # 1h
	run_on_start=bool(testmode()),
)
async def inactivity_loop():
	logger.debug("Checking for user inactivity...")

	after = S.tz_now() - Δ(days=30)

	# todo: convert into a cache, populated once at bot boot, and kept up to date with events like MessageCreatedEvent, later this loop should only check the up to date cache every like 1hr to check if user has not been active.
	inactive_members = await fetch_inactive_members_of_own_guilds(
		BOT.rest.fetch_my_guilds(newest_first=False),
		after=after,
	)

	fmt = nya_fmt.Formatter(
		no_quoteless_str=True,
	)

	logger.info(
		"Found inactive members in %d guilds.\n%s",
		len(inactive_members),
		fmt(inactive_members),
	)

	# todo: REMOVE ONLY RIGHT BEFORE RELEASE: confirm that this does NOT auto-ban users, but rather notify administrators, you should not trust yourself with auto-bans because any bug in the code might falsely ban half the server...
