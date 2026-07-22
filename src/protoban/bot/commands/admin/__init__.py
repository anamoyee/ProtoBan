from ....get_logger import get_logger
from . import ban_reason as ban_reason
from . import logs_channel as logs_channel
from . import stats as stats
from . import version as version

get_logger(__name__).info(  # ruff:ignore[non-empty-init-module]
	"Loaded subcommands: %s",
	", ".join([
		f"/{__name__.split(".")[-1]} {name}"  #
		for name, obj in locals().items()
		if (
			isinstance(obj, __import__("types").ModuleType)  #
			and not name.startswith("_")
		)
	]),
)
