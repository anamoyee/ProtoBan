# from . import ping as ping # keep ping.py file as template for future commands, but don't load it
from ...get_logger import get_logger
from . import _error_handler as _error_handler
from . import admin as admin

get_logger(__name__).info(  # ruff:ignore[non-empty-init-module]
	"Loaded commands: %s",
	", ".join([
		f"/{name}"  #
		for name, obj in locals().items()
		if (
			isinstance(obj, __import__("types").ModuleType)  #
			and not name.startswith("_")
		)
	]),
)
