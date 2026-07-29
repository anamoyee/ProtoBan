from typing import TYPE_CHECKING, Any

import hikari

from ...get_logger import get_logger
from ..bot import BOT
from .bound import BoundOnlyViewMixin

if TYPE_CHECKING:
	import arc
	import miru

_cleanup_on_shutdown: list[TimeoutClearItemsViewMixin] = []

logger = get_logger(__name__)


class TimeoutClearItemsViewMixin(BoundOnlyViewMixin):
	_response: arc.InteractionResponse | None = None

	def __init__(self, *args: Any, **kwargs: Any):
		super().__init__(*args, **kwargs)

		_cleanup_on_shutdown.append(self)

	def provide_response_for_ephemeral_on_timeout(self, response: arc.InteractionResponse):
		"""ctx.message does not work to edit the message on timeout for ephemeral messages, if message is ephemeral, you need to call this somewhere before starting the view."""
		self._response = response

	def _client_start_hook(self, client: miru.Client) -> None:
		super()._client_start_hook(client)

		if self.message.flags & hikari.MessageFlag.EPHEMERAL and self._response is None:
			msg_1 = "TimeoutClearButtonsViewMixin cannot be started bound to an ephemeral message, unless you call provide_response_for_ephemeral_on_timeout(...) before starting the view."
			e = RuntimeError(msg_1)
			e.add_note(f"view={self!r}")
			raise e

	async def on_timeout(self) -> None:
		await super().on_timeout()

		assert self.message is not None

		if self in _cleanup_on_shutdown:
			_cleanup_on_shutdown.remove(self)

		self.clear_items()

		if self._response is not None:
			await self._response.edit(components=self)
		else:
			await self.message.edit(components=self)


@BOT.listen(hikari.StoppingEvent)
async def _on_stopping(event: hikari.StoppingEvent) -> None:
	if len_cleanup_on_shutdown := len(_cleanup_on_shutdown) == 0:
		logger.info("cleaning up %d `miru.View`s", len_cleanup_on_shutdown)

	for view in _cleanup_on_shutdown:  # don't `asyncio.gather` as this will stress the network (and possibly 429)
		logger.debug("cleaning up view: %r", view)
		await view.on_timeout()
