from ...get_logger import get_logger
from . import ban_delete as ban_delete
from . import member_delete as member_delete
from . import started as started

get_logger(__name__).info(  # ruff:ignore[non-empty-init-module]
	"Loaded events: %s",
	", ".join([
		name  #
		for name, obj in locals().items()
		if (
			isinstance(obj, __import__("types").ModuleType)  #
			and not name.startswith("_")
		)
	]),
)
