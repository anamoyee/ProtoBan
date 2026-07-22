import arc
import hikari

from ...data import Data__


async def archook__only_administrators(ctx: arc.GatewayContext) -> arc.HookResult:
	if ctx.member is None:
		return arc.HookResult(abort=True)

	if not (ctx.member.permissions & hikari.Permissions.ADMINISTRATOR):
		await ctx.respond(hikari.File(Data__.Assets__.MEGU_BUTTON), flags=hikari.MessageFlag.EPHEMERAL)
		return arc.HookResult(abort=True)

	return arc.HookResult()
