import datetime as dt

from nya_scope import Scope as _Scope  # alias to prevent missclicks Scope instead of S when tab completing


class S(_Scope):
	EMOJI_OK: str = "✅"
	EMOJI_ERR: str = "❌"
	EMOJI_WARN: str = "⚠️"

	TZ = dt.datetime.now().astimezone().tzinfo  # get the local timezone of the system running the bot
