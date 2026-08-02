import hikari

from ..bot import BOT
from .inactivity import inactivity_loop


@BOT.listen(hikari.StartedEvent)
async def start_loops(_: hikari.StartedEvent) -> None:
	inactivity_loop.start()

	# todo: move inactivity_loop.start() to its own event (inactivity.py) as it requires populating the database before it runs;
	#       loops should not all be started in the same start_loops event as it's really their own thing, and any setup required should be up to them (in their .py file)
