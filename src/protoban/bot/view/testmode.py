from typing import Any

from ...environment import testmode
from ._base import View


class TestmodeShorterTimeoutViewMixin(View):
	def __init__(self, *args: Any, **kwargs: Any):
		super().__init__(*args, **kwargs)

		if self.timeout is not None and testmode():
			self._timeout: int | float | None = max(5, self.timeout / 60)  # turn minutes into seconds, at least 5 seconds tho
