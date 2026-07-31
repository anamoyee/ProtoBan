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

	await ctx.defer(hikari.MessageFlag.EPHEMERAL)

	banned_users: dict[hikari.Snowflake, tuple[str, str]] = Data__.read_banned_users(ctx.guild_id)

	bytes_ = hikari.Bytes(
		json.dumps(
			[
				EntryDict(
					user_id=str(user_id),
					username=username,
					reason=reason,
				)
				for user_id, (username, reason) in banned_users.items()
			],
			indent=4,
		).encode("utf-8"),
		f"ban_statistics_{dt.datetime.now(tz=S.TZ):%Y-%m-%d_%H-%M-%S}.json",
	)

	await ctx.respond(
		embed=hikari.Embed(
			title="ProtoBan Stats",
			description=f"""
Total ProtoBan auto-bans: `{len(banned_users)}`
Total bans on the server: `{len(await ctx.client.app.rest.fetch_bans(ctx.guild_id))}`
"""[1:-1],
		),
		attachment=bytes_,
		flags=hikari.MessageFlag.EPHEMERAL,
	)
