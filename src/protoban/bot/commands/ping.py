import arc

from ..bot import ACL


@ACL.include
@arc.slash_command("ping", "Check if the bot is alive.")
async def cmd_ping(ctx: arc.GatewayContext) -> None:
	await ctx.respond("Pong!")
