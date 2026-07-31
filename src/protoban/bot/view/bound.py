from typing import TYPE_CHECKING

from ._base import View

if TYPE_CHECKING:
	import hikari
	import miru


class BoundOnlyViewMixin(View):
	"""Will raise a RuntimeError on miru.Client().start_view(...) if the view is not bound to a message."""

	@property
	def message(self) -> hikari.Message:
		super_message = super().message
		assert super_message is not None  # should never be None
		return super_message

	def _client_start_hook(self, client: miru.Client) -> None:
		super()._client_start_hook(client)

		if self._message is None:
			msg_0 = "BoundOnlyViewMixin requires to be bound to a message. Remove this mixin from the definition or add a bind_to=... in miru.Client().start_view(...)"
			raise RuntimeError(msg_0)


class UnboundOnlyViewMixin(View):
	"""Will raise a RuntimeError on miru.Client().start_view(...) if the view is bound to a message."""

	@property
	def message(self) -> None:
		super_message = super().message
		assert super_message is None  # should always be None in an unbound view
		return super_message

	def _client_start_hook(self, client: miru.Client) -> None:
		super()._client_start_hook(client)

		if self._message is not None:
			msg_0 = "UnboundOnlyViewMixin requires to NOT be bound to a message. Remove this mixin from the definition or remove the bind_to=... in miru.Client().start_view(...)"
			raise RuntimeError(msg_0)
