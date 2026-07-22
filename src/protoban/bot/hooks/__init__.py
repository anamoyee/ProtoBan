from ...get_logger import get_logger
from . import permissions as permissions

get_logger(__name__).info(  # ruff:ignore[non-empty-init-module]
	"Loaded hooks: %s",
	", ".join([
		name  #
		for name, obj in locals().items()
		if (
			isinstance(obj, __import__("types").ModuleType)  #
			and not name.startswith("_")
		)
	]),
)
