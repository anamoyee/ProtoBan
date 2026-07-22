import hikari

from ...get_logger import get_logger
from ..bot import BOT, testmode

logger = get_logger(__name__)


async def setup_initial_activity_and_status(bot: hikari.GatewayBot) -> None:
	await bot.update_presence(
		activity=hikari.Activity(
			name="🐈 meows at u" + testmode(),
			type=hikari.ActivityType.CUSTOM,
		),
		status=hikari.Status.IDLE if testmode() else hikari.Status.DO_NOT_DISTURB,
	)


@BOT.listen(hikari.StartedEvent)
async def on_started(ev: hikari.StartedEvent) -> None:
	await setup_initial_activity_and_status(BOT)

	if testmode():
		# .debug() should itself be in testmode only, but might as well check `if testmode()`, if this behaviour ever changes or is overriden manually
		logger.debug("*** Started in testmode ***")
