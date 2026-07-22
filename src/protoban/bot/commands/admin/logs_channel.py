import arc
import hikari

from ....data import Data__
from ...settings import S
from ._group import slash_group as __slash_group

slash_subgroup = __slash_group.include_subgroup("logs-channel", "Configure the logs channel for the bot.")


@slash_subgroup.include
@arc.slash_subcommand("view", "View the current logs channel.")
async def subcmd_admin__logs_channel__view(ctx: arc.GatewayContext) -> None:
	if not ctx.guild_id:
		await ctx.respond(f"{S.EMOJI_ERR} This command can only be used in a guild.", flags=hikari.MessageFlag.EPHEMERAL)
		return

	channel_id = Data__.read_logs_channel(ctx.guild_id)

	if channel_id is None:
		await ctx.respond(
			f"{S.EMOJI_WARN} The logs channel for this server is currently unset, set one with {subcmd_admin__logs_channel__set.make_mention(ctx.guild_id)}.",
			flags=hikari.MessageFlag.EPHEMERAL,
		)
		return

	await ctx.respond(f"{S.EMOJI_OK} The logs channel for this server is currently set to <#{channel_id}>.", flags=hikari.MessageFlag.EPHEMERAL)


@slash_subgroup.include
@arc.slash_subcommand("set", "Set the logs channel for the bot.")
async def subcmd_admin__logs_channel__set(
	ctx: arc.GatewayContext,
	*,
	channel: arc.Option[hikari.TextableGuildChannel, arc.ChannelParams("The channel to set as the logs channel.")],
) -> None:
	if not ctx.guild_id:
		await ctx.respond(f"{S.EMOJI_ERR} This command can only be used in a guild.", flags=hikari.MessageFlag.EPHEMERAL)
		return

	Data__.write_logs_channel(guild_id=ctx.guild_id, new_channel_id=channel.id)

	await ctx.respond(f"{S.EMOJI_OK} Successfully set the logs channel for this server to <#{channel.id}>.", flags=hikari.MessageFlag.EPHEMERAL)


@slash_subgroup.include
@arc.slash_subcommand("unset", "Unset the logs channel for the bot.")
async def subcmd_admin__logs_channel__unset(ctx: arc.GatewayContext) -> None:
	if not ctx.guild_id:
		await ctx.respond(f"{S.EMOJI_ERR} This command can only be used in a guild.", flags=hikari.MessageFlag.EPHEMERAL)
		return

	Data__.unlink_logs_channel(ctx.guild_id)

	await ctx.respond(f"{S.EMOJI_OK} Successfully unset the logs channel for this server.", flags=hikari.MessageFlag.EPHEMERAL)
