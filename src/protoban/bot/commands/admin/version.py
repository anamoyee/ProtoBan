import arc
import hikari

from ...._version import __version__
from ....environment import testmode
from ._group import slash_group


def testmode_text_only() -> str:
	"""Return ' - Testmode' if in testmode, '' otherwise."""
	return " - Testmode" if testmode() else ""


@slash_group.include
@arc.slash_subcommand("view-version", "View the current version of the bot.")
async def subcmd_admin__view_version(ctx: arc.GatewayContext) -> None:
	if __package__ is None:
		msg = "__package__ is None, expected this app to be packaged, do not run the app without packaging."
		raise AssertionError(msg)  # not using assert because i want this to keep being raised even in -OO

	await ctx.respond(
		f"`{__package__.split(".", maxsplit=1)[0].replace("`", "'")}` `v{__version__}`{testmode_text_only()}",
		flags=hikari.MessageFlag.EPHEMERAL,
	)
