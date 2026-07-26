import asyncio
import csv
import datetime as dt
import io
from dataclasses import dataclass

import aiohttp
import arc
import hikari
import miru
from nya_codeblock import codeblock, codeblocks
from nya_extract_error import extract_error

from ....environment import testmode
from ....get_logger import get_logger
from ...bot import MCL
from ...settings import S
from ._group import slash_group as __slash_group

slash_subgroup = __slash_group.include_subgroup("mass-ban", "Perform mass bans from a file")

logger = get_logger(__name__)


async def _async_download_file_to_str(url: str) -> str:
	"""Asynchronously downloads a file from a URL and returns its contents as a string without saving it to the disk.

	Args:
		url (str): The URL of the file to download.

	Returns:
		str: The contents of the downloaded file as a string.

	Raises:
		RuntimeError: If the download fails.
	"""
	try:
		async with aiohttp.ClientSession() as session, session.get(url) as response:
			response.raise_for_status()

			return await response.text()
	except aiohttp.ClientResponseError as e:
		msg = f"Failed to download file from {url=}: {e}"
		raise RuntimeError(msg) from e


@dataclass(kw_only=True)
class _PartialBan:
	user_id: hikari.Snowflake
	reason: str


class _UpdateUserProgressEditResponse:
	def __init__(
		self,
		ctx: arc.GatewayContext,
		*,
		minimum_delay_between_updates: dt.timedelta = dt.timedelta(seconds=1),
		ephemeral: bool = True,
	):
		self._ctx = ctx
		self._minimum_delay_between_updates = minimum_delay_between_updates

		self._pending = None
		self._done_lst = []
		self._last_update = None
		self.ephemeral = ephemeral

	_pending: str | None
	_done_lst: list[str]
	_last_update: dt.datetime | None

	async def update(self, new_pending: str | None):
		if self._pending is None and new_pending is None:
			return  # no change

		if self._pending is not None:
			self._done_lst.append(self._pending)
		self._pending = new_pending

		message_text = "\n".join(f"✅ {done}" for done in self._done_lst)
		if self._pending:
			message_text += f"\n⏳ {self._pending}"

		if not message_text:
			return  # avoid empty content error

		if self._last_update is not None:
			δ = dt.datetime.now(S.TZ) - self._last_update

			if δ < self._minimum_delay_between_updates:
				await asyncio.sleep((self._minimum_delay_between_updates - δ).total_seconds())

		if not self._ctx.issued_response:
			await self._ctx.respond(message_text, flags=hikari.MessageFlag.EPHEMERAL if self.ephemeral else hikari.MessageFlag.NONE)
		else:
			await self._ctx.edit_initial_response(message_text)


async def _mass_ban_impl(
	ctx: arc.GatewayContext,
	/,
	*bans: _PartialBan,
	progress: _UpdateUserProgressEditResponse,
) -> None:
	assert ctx.guild_id is not None, "This command can only be used in a guild context."

	await progress.update("Fetching current members of the server to check for active bans")
	_ban_ids = {ban.user_id for ban in bans}
	members_to_ban: list[hikari.Member] = [member async for member in ctx.client.app.rest.fetch_members(ctx.guild_id) if member.id in _ban_ids]

	description = f"Parsed `{len(bans)}` records"

	if members_to_ban:
		description += f", of which `{len(members_to_ban)}` are current members of the server and will be banned:"
		description += "\n" + ", ".join(member.mention for member in members_to_ban)
	else:
		description += " (No current server members will be banned)."

	PREVIEW_LENGTH = 3
	description += codeblocks(*(f"{b.user_id},{b.reason!r}" for b in bans[:PREVIEW_LENGTH]), max_length=1000, langcodes=("csv",) * PREVIEW_LENGTH)
	if len(bans) > PREVIEW_LENGTH:
		description += f"(and {len(bans) - PREVIEW_LENGTH} more)\n"

	embed = hikari.Embed(
		title="🔨 Mass Ban Tool",
		description=description,
		color=0xFF8000,
	)

	await ctx.edit_initial_response(embed=embed)


class ConfirmMassBanView(miru.View):
	pass  # todo: impl


@slash_subgroup.include
@arc.slash_subcommand("csv", "Perform mass bans from a file (try to interpret the file as csv)")
async def subcmd_admin__mass_ban__csv(
	ctx: arc.GatewayContext,
	*,
	file: arc.Option[hikari.Attachment, arc.AttachmentParams("A csv file containing the users to ban")],
	default_ban_reason: arc.Option[
		str,
		arc.StrParams("The default ban reason to use if none is provided for the given entry"),
	] = "No reason provided.",
	ban_reason_prefix: arc.Option[
		str,
		arc.StrParams("If any, prepend this string to all ban reasons (incl. the default_ban_reason)"),
	] = "ProtoBan mass-ban: ",
	mark_as_protoban_autobans: arc.Option[  # todo: impl
		bool,
		arc.BoolParams("Whether to add the bans into the protoban database, or treat them as regular bans."),
	] = False,
):
	await ctx.defer(hikari.MessageFlag.EPHEMERAL)

	progress = _UpdateUserProgressEditResponse(ctx, ephemeral=True)
	await progress.update("Downloading & parsing attachment")

	content = await _async_download_file_to_str(file.url)

	bans: list[_PartialBan] = []

	try:
		reader = csv.reader(io.StringIO(content))

		for i, row in enumerate(reader, start=1):
			if not row:  # Skip empty lines
				continue

			if len(row) > 2:
				msg_0 = f"Line {i}: expected at most 2 columns (user_id, reason), got {len(row)}."
				raise ValueError(msg_0)  # ruff: ignore[raise-within-try]

			raw_user_id = row[0].strip()

			try:
				user_id = hikari.Snowflake(raw_user_id)
			except ValueError as e:
				msg_1 = f"Line {i}: invalid user_id '{raw_user_id}' (must be a valid Discord integer Snowflake)."
				raise ValueError(msg_1) from e

			# Extract reason or fall back to default if blank or 1-column row
			user_reason = row[1].strip() if len(row) == 2 else default_ban_reason

			if not user_reason:
				user_reason = default_ban_reason

			bans.append(_PartialBan(user_id=user_id, reason=f"{ban_reason_prefix}{user_reason}"))

		if not bans:
			msg_2 = "The provided CSV file contains no valid entries."
			raise ValueError(msg_2)  # ruff: ignore[raise-within-try]

	except (csv.Error, ValueError, IndexError) as e:
		await ctx.respond(
			f"""
Failed to parse csv file. Make sure your data is a **headerless**, 2-column csv file where the first column is `user_id` (`int`) and the second column is `reason` (`str`).
{codeblock(extract_error(e))}
"""[1:-1],
		)

		return

	logger.debug("Parsed CSV file into %d `_PartialBan`s", len(bans))
	await _mass_ban_impl(ctx, *bans, progress=progress)


if testmode():

	@slash_subgroup.include
	@arc.slash_subcommand("on-test-data", "Perform the mass ban impl on some test data.")
	async def subcmd_admin__mass_ban__on_test_data(ctx: arc.GatewayContext):
		pass
