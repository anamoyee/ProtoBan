from urllib.parse import quote

import arc
import hikari
from nya_codeblock import codeblock

from ....data import Data__
from ...settings import S
from ._group import slash_group

slash_subgroup = slash_group.include_subgroup("ban-reason", "View or change the ban reason.")


@slash_subgroup.include
@arc.slash_subcommand("set", "Set the ban reason.")
async def subcmd_admin__ban_reason__set(
	ctx: arc.GatewayContext,
	*,
	new_reason: arc.Option[
		str,
		arc.StrParams(
			"The reason to set.",
			max_length=512,  # discord's limit; see https://docs.discord.com/developers/resources/audit-log#:~:text=Apps%20can%20specify,with%20the%20API.
		),
	],
) -> None:
	if ctx.guild_id is None:
		await ctx.respond(
			f"{S.EMOJI_ERR} This command can only be used in a guild.",
			flags=hikari.MessageFlag.EPHEMERAL,
		)
		return

	new_reason_urlencoded = quote(new_reason, safe="")
	if len(new_reason_urlencoded) > 512:
		# discord's limit; see https://docs.discord.com/developers/resources/audit-log#:~:text=Apps%20can%20specify,with%20the%20API.
		await ctx.respond(
			f"{S.EMOJI_ERR} Reason is too long after urlencoding (len=`{len(new_reason_urlencoded)}`), this is a discord limitation and not an arbitrary limitation of the bot.",
			flags=hikari.MessageFlag.EPHEMERAL,
		)
		return

	Data__.write_ban_reason(guild_id=ctx.guild_id, new_reason=new_reason)

	await ctx.respond(
		f"{S.EMOJI_OK} Successfully set ban reason to:\n{codeblock(new_reason, max_length=1000, convert_three_backticks_to_apostrophes=True)}",
		flags=hikari.MessageFlag.EPHEMERAL,
	)


@slash_subgroup.include
@arc.slash_subcommand("view", "View the current ban reason.")
async def subcmd_admin__ban_reason__view(
	ctx: arc.GatewayContext,
) -> None:
	if ctx.guild_id is None:
		await ctx.respond(
			f"{S.EMOJI_ERR} This command can only be used in a guild.",
			flags=hikari.MessageFlag.EPHEMERAL,
		)
		return

	current_reason = Data__.read_ban_reason(ctx.guild_id)

	await ctx.respond(
		f"{S.EMOJI_OK} Current ban reason:\n{codeblock(current_reason, max_length=1000, convert_three_backticks_to_apostrophes=True)}",
		flags=hikari.MessageFlag.EPHEMERAL,
	)


@slash_subgroup.include
@arc.slash_subcommand("unset", "Unset the ban reason.")
async def subcmd_admin__ban_reason__unset(
	ctx: arc.GatewayContext,
) -> None:
	if ctx.guild_id is None:
		await ctx.respond(
			f"{S.EMOJI_ERR} This command can only be used in a guild.",
			flags=hikari.MessageFlag.EPHEMERAL,
		)
		return

	Data__.unlink_ban_reason(ctx.guild_id)

	await ctx.respond(
		f"{S.EMOJI_OK} Successfully unset ban reason.",
		flags=hikari.MessageFlag.EPHEMERAL,
	)
