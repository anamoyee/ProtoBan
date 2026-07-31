import miru
import miru.abc.item

from ...get_logger import get_logger

logger = get_logger(__name__)


class View(miru.View):
	async def on_error(
		self,
		error: Exception,
		item: miru.abc.item.InteractiveViewItem | None = None,
		context: miru.ViewContext | None = None,
		/,
	) -> None:
		if item:
			logger.error("Ignoring exception in view %s for item %s", self, item, exc_info=error)
		else:
			logger.error("Ignoring exception in view %s", self, exc_info=error)
