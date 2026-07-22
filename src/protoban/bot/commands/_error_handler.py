from typing import TYPE_CHECKING

import hikari

from ...environment import testmode
from ..bot import ACL

if TYPE_CHECKING:
	import arc
from ...get_logger import get_logger

logger = get_logger(__name__)


@ACL.set_error_handler
async def error_handler(ctx: arc.GatewayContext, e: Exception) -> None:
	await ctx.respond(
		f"**Error!**{" Check the logs for more information & the traceback." if testmode() else ""}", flags=hikari.MessageFlag.EPHEMERAL
	)

	logger.exception(  # ruff:ignore[log-exception-outside-except-handler]
		"Error in command %r: %r",
		ctx.command.display_name,
		e,
		exc_info=(type(e), e, e.__traceback__),
	)
	# this is an exception handler, but pulled out to a fn (ad. ruff ignore above)
