import datetime as dt
import json
from typing import TypedDict

import arc
import hikari

from ....data import Data__
from ...settings import S
from ._group import slash_group


class EntryDict(TypedDict):
	user_id: str
	username: str
	reason: str


@slash_group.include
@arc.slash_subcommand("stats", "View the statistics of banned users.")
async def subcmd__admin__stats(ctx: arc.GatewayContext):
	if ctx.guild_id is None:
		await ctx.respond(
			f"{S.EMOJI_ERR} This command can only be used in a guild.",
			flags=hikari.MessageFlag.EPHEMERAL,
		)
		return

	banned_users: dict[hikari.Snowflake, tuple[str, str]] = Data__.read_banned_users(ctx.guild_id)

	attachment_content = json.dumps(
		[
			EntryDict(
				user_id=str(user_id),
				username=username,
				reason=reason,
			)
			for user_id, (username, reason) in banned_users.items()
		],
		indent=4,
	)

	bytes_ = hikari.Bytes(attachment_content.encode("utf-8"), f"ban_statistics_{dt.datetime.now(tz=S.TZ):%Y-%m-%d_%H-%M-%S}.json")

	components = [
		hikari.impl.ContainerComponentBuilder(
			components=[
				hikari.impl.TextDisplayComponentBuilder(content="# 🔨 Ban Statistics"),
			]
		),
		hikari.impl.ContainerComponentBuilder(
			components=[
				hikari.impl.TextDisplayComponentBuilder(content=f"Total auto-banned users: `{len(banned_users)}`"),
			]
		),
		hikari.impl.FileComponentBuilder(file=bytes_),
	]

	await ctx.respond(
		components=components,
		# attachment=bytes_,
		flags=hikari.MessageFlag.EPHEMERAL | hikari.MessageFlag.IS_COMPONENTS_V2,
	)
