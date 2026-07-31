import asyncio
import csv
import datetime as dt
import io
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

import aiohttp
import arc
import hikari
import miru
from aiolimiter import AsyncLimiter
from nya_codeblock import codeblock, codeblocks
from nya_extract_error import extract_error

from ....data import Data__
from ....environment import testmode
from ....get_logger import get_logger
from ... import view as vmix
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

			content_bytes = await response.read()

			for encoding in ("utf-8", "utf-16", "utf-8-sig", "cp1252"):
				try:
					return content_bytes.decode(encoding)
				except UnicodeDecodeError:
					continue

			return content_bytes.decode("utf-8", errors="replace")
	except aiohttp.ClientResponseError as e:
		msg = f"Failed to download file from {url=}: {e}"
		raise RuntimeError(msg) from e


@dataclass(kw_only=True, frozen=True)
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

		_now = dt.datetime.now(S.TZ)
		if self._last_update is not None:
			δ = _now - self._last_update

			if δ < self._minimum_delay_between_updates:
				await asyncio.sleep((self._minimum_delay_between_updates - δ).total_seconds())
		self._last_update = _now

		if not self._ctx.issued_response:
			await self._ctx.respond(message_text, flags=hikari.MessageFlag.EPHEMERAL if self.ephemeral else hikari.MessageFlag.NONE)
		else:
			await self._ctx.edit_initial_response(message_text)


class CommitMassBanView(
	vmix.TestmodeShorterTimeout,
	vmix.TimeoutDisableItems,
	vmix.BoundOnly,
	vmix.View,
):
	def __init__(
		self,
		*,
		bans: Sequence[_PartialBan],
		invoker_id: hikari.Snowflake,
	):
		self.bans = bans
		self.invoker_id = invoker_id
		super().__init__(timeout=(5 * 60))

	async def perform_bannage(self, ctx: miru.ViewContext) -> None:
		assert ctx.guild_id is not None

		ii = len(self.bans)

		failed_bans: dict[_PartialBan, BaseException] = {}

		def make_failed_bans_codeblocks() -> str:
			header_str = "\n"

			return header_str + codeblocks(
				*(
					f"{ban.user_id}: {extract_error(e)}"  #
					for ban, e in failed_bans.items()
				),
				max_length=2000 - (7 * len(failed_bans)) - len(header_str),
			)

		def content_to_edit_embeds(
			content: str,
			*,
			in_progress: bool = False,
		) -> tuple[hikari.Embed, ...]:
			warning_embed_tuple_or_empty_tuple = (
				(
					hikari.Embed(
						title="‼️ High volume of bans requested",
						description="If the progress stops updating in the pending stage, approximately 15 minutes after the start of interation, it is likely that due to Discord's limitation of finite lifespan of a discord slashcommand interaction it has expired, and the bot cannot issue further edits to the message.\n\nIn this case the bot will try to silently finish the banning process, but its further failures and the finished status cannot be added (by editing) to the interaction message.\n\nWhile new messages can be created in the same channel, ephemeral ('Only you can see this') type of messages cannot, therefore i did not take this route of just spawning a new message.\n\n**If you experience this issue, try splitting your data in two or three smaller chunks.**",
						color=0xFF0000,
					),
				)
				if len(self.bans) >= 300
				else ()
			)

			embed = hikari.Embed(
				title="Mass Ban Results",
				color=0x0000FF if in_progress else (0x00FF00 if not failed_bans else 0xFFFF00),
				description=content[:4096],  # Discord allows a maximum of 4096 characters in an embed description
			)

			final_embeds = (*ctx.message.embeds, *warning_embed_tuple_or_empty_tuple, embed)

			assert len(final_embeds) <= 10  # Discord allows a maximum of 10 embeds per message
			return final_embeds

		# try to avoid hitting discord's limits for 'BadRequestError: Bad Request 400: (30035) 'Max number of bans for non-guild members have been exceeded. Try again later' for https://discord.com/api/v10/guilds/.../bans/...'
		limiter = AsyncLimiter(1, 1)
		for i, ban in enumerate(self.bans, start=1):
			logger.debug("%0*d/%d Mass-banning user %r", len(str(len(self.bans))), i, len(self.bans), ban.user_id)

			try:
				await limiter.acquire()
				await ctx.client.app.rest.ban_user(
					ctx.guild_id,
					ban.user_id,
					reason=ban.reason,
				)
			except Exception as e:
				failed_bans[ban] = e

			UPDATE_EVERY_N_BANS = 25
			if (i == 1 or i % UPDATE_EVERY_N_BANS == 0) and i != ii:  # update progress every 25 bans
				in_progress_content = f"""
⏳ Banning in progress {" with failures" if failed_bans else ""}... `{i:0{len(str(ii))}d}/{ii}` done{f" (of which `{len(failed_bans)}` failed)" if failed_bans else ""}.
-# with a rate limiter of `{limiter.max_rate / limiter.time_period:g}` ban per second
-# updates to this message issued every about `{UPDATE_EVERY_N_BANS}` bans
"""[1:-1]

				if failed_bans:
					in_progress_content += make_failed_bans_codeblocks()

				try:
					await ctx.edit_response(
						embeds=content_to_edit_embeds(in_progress_content, in_progress=True),
					)
				except hikari.UnauthorizedError:
					logger.warning(
						"Received hikari.UnauthorizedError while trying to update status for mass ban progress for guild_id=%r, did the interaction expire? Continuing ...",
						ctx.guild_id,
					)

		finished_content = f"""
{S.EMOJI_OK if not failed_bans else S.EMOJI_WARN} Banning finished{" with failures" if failed_bans else ""}. `{ii}` done{f" (of which `{len(failed_bans)}` failed)" if failed_bans else ""}.
"""[1:-1]

		if failed_bans:
			finished_content += make_failed_bans_codeblocks()

		attachment = (
			hikari.UNDEFINED
			if len(finished_content) <= 4096
			else hikari.Bytes(
				finished_content.encode("utf-8"),
				"progress_log.txt",
			)
		)

		self.clear_items()  # so later the view's on_timeout doesnt add the components back to the message as part of the vmix.TimeoutDisableItems
		try:
			await ctx.edit_response(
				embeds=content_to_edit_embeds(finished_content),
				attachment=attachment,
				components=[],
			)
		except hikari.UnauthorizedError:
			logger.warning(
				"Received hikari.UnauthorizedError while trying to update status for mass ban finished for guild_id=%r, did the interaction expire? Continuing ...",
				ctx.guild_id,
			)

	@miru.button(label="Commit", style=hikari.ButtonStyle.DANGER)
	async def btn_commit(self, ctx: miru.ViewContext, btn: miru.Button):
		assert isinstance(ctx.view, CommitMassBanView)

		if self.invoker_id != ctx.user.id:
			await ctx.respond(Data__.Assets__.MEGU_BUTTON(), flags=hikari.MessageFlag.EPHEMERAL)
			return

		await self.on_timeout()

		await self.perform_bannage(ctx)

	@miru.button(label="Cancel", style=hikari.ButtonStyle.SECONDARY)
	async def btn_cancel(self, ctx: miru.ViewContext, btn: miru.Button):
		assert isinstance(ctx.view, CommitMassBanView)

		if self.invoker_id != ctx.user.id:
			await ctx.respond(Data__.Assets__.MEGU_BUTTON(), flags=hikari.MessageFlag.EPHEMERAL)
			return

		await self.on_timeout()


class DuplicatesPolicy(StrEnum):
	SKIP = "skip"
	FAIL = "fail"


async def _mass_ban_impl(
	ctx: arc.GatewayContext,
	/,
	*bans: _PartialBan,
	progress: _UpdateUserProgressEditResponse,
	duplicates_policy: DuplicatesPolicy,
) -> None:
	ban_ids_seen = set()
	new_bans = []

	for ban in bans:
		if ban.user_id in ban_ids_seen:
			match duplicates_policy:
				case DuplicatesPolicy.SKIP:
					logger.debug("%r: Skipping duplicate user_id: %r", duplicates_policy, ban.user_id)
					continue
				case DuplicatesPolicy.FAIL:
					logger.debug("%r: Failing due to duplicate user_id: %r", duplicates_policy, ban.user_id)
					await (ctx.edit_initial_response if ctx.issued_response else ctx.respond)(
						f"{S.EMOJI_ERR} Duplicate user_id found in the provided data: `{ban.user_id!r}`."
					)
					return
				case rest:
					assert_never(rest)

		ban_ids_seen.add(ban.user_id)
		new_bans.append(ban)

	assert ctx.guild_id is not None, "This command can only be used in a guild context."

	await progress.update("Fetching members of the server to check for active bans")

	_ban_ids = {ban.user_id for ban in bans}
	members_to_ban: list[hikari.Member] = [member async for member in ctx.client.app.rest.fetch_members(ctx.guild_id) if member.id in _ban_ids]

	description = f"Parsed **`{len(bans)!r}`** records"

	if members_to_ban:
		description += f", of which **`{len(members_to_ban)!r}`** are members of the server and will be banned:"
		description += "\n" + ", ".join(member.mention for member in members_to_ban)
	else:
		description += "\n(No server members will be banned, only users that are not currently here)."

	PREVIEW_MAX_LENGTH = 3
	preview_slice = bans[:PREVIEW_MAX_LENGTH]
	description += codeblocks(
		*(
			f"{b.user_id},{b.reason!r}"  #
			for b in preview_slice
		),
		max_length=2000,
		langcodes="csv",
	)
	if len(bans) > PREVIEW_MAX_LENGTH:
		description += f"(and {len(bans) - PREVIEW_MAX_LENGTH} more)\n"

	embed = (
		hikari
		.Embed(
			title="🔨 Mass Ban Summary",
			description=description,
			color=0xFF8000,
		)
		.set_author(
			name=ctx.author.display_name or ctx.author.global_name or ctx.author.username,
			icon=ctx.author.make_avatar_url() or ctx.author.default_avatar_url,
		)
		.set_footer("If this looks good, please confirm the mass ban operation by clicking the button below.")
	)

	view = CommitMassBanView(
		bans=bans,
		invoker_id=ctx.user.id,
	)

	await ctx.edit_initial_response(
		content="",  # clear progress responses
		embed=embed,
		components=view.build(),
	)

	response = await ctx.get_last_response()
	message = await response

	view.provide_response_for_ephemeral_on_timeout(response)
	MCL.start_view(view, bind_to=message)


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
	duplicates_policy_str: arc.Option[
		str,
		arc.StrParams(
			"How to handle duplicate entries (by user_id), if 'skip', the reason may be either of the entries'.",
			name="duplicates_policy",
			choices=("skip", "fail"),
		),
	] = "fail",
	ephemeral: arc.Option[
		bool,
		arc.BoolParams("Hide the message(s)."),
	] = True,
):
	progress = _UpdateUserProgressEditResponse(ctx, ephemeral=ephemeral)
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
				msg_1 = f"Line {i}: invalid user_id '{raw_user_id}' (must be a valid Discord integer ID/Snowflake)."
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
	await _mass_ban_impl(
		ctx,
		*bans,
		progress=progress,
		duplicates_policy=DuplicatesPolicy(duplicates_policy_str),
	)


if testmode():

	@slash_subgroup.include
	@arc.slash_subcommand("unban-everyone", "Unban everyone in the server (for testing purposes only!!).")
	async def subcmd_admin__mass_ban__unban_everyone(ctx: arc.GatewayContext):
		if ctx.guild_id is None:
			await ctx.respond(
				f"{S.EMOJI_ERR} This command can only be used in a guild.",
				flags=hikari.MessageFlag.EPHEMERAL,
			)
			return

		await ctx.defer(flags=hikari.MessageFlag.EPHEMERAL)

		bans = await ctx.client.app.rest.fetch_bans(ctx.guild_id)
		ii = len(bans)

		await ctx.respond(
			f"{S.EMOJI_WARN} Unbanning everyone in the server, total bans: `{ii}`. This may take a while...",
		)

		for i, ban in enumerate(bans):
			logger.debug("%0*d/%d Unbanning user %r", len(str(ii)), i, ii, ban.user.id)
			await ctx.client.app.rest.unban_user(ctx.guild_id, ban.user.id)

		await ctx.edit_initial_response(
			f"{S.EMOJI_OK} Unbanned everyone in the server. Total unbanned: `{ii}`",
		)

	@slash_subgroup.include
	@arc.slash_subcommand("on-test-data", "Perform the mass ban impl on some test data.")
	async def subcmd_admin__mass_ban__on_test_data(ctx: arc.GatewayContext):
		await _mass_ban_impl(
			ctx,
			*(
				_PartialBan(user_id=hikari.Snowflake(123456789012345678), reason="Test reason 1"),
				_PartialBan(user_id=hikari.Snowflake(733653090267299890), reason="Test reason 2"),
			),
			progress=_UpdateUserProgressEditResponse(ctx, ephemeral=True),
			duplicates_policy=DuplicatesPolicy.SKIP,
		)
