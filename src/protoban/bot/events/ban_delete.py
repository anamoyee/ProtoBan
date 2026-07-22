import hikari

from ...data import Data__
from ...get_logger import get_logger
from ..bot import BOT

logger = get_logger(__name__)


@BOT.listen(hikari.BanDeleteEvent)
async def on_ban_delete(ev: hikari.BanDeleteEvent) -> None:
	banned_user = Data__.read_banned_user(guild_id=ev.guild_id, user_id=ev.user_id)

	if banned_user is None:
		return  # no record, probably not an autoban -> doesnt matter to us

	Data__.remove_banned_user(guild_id=ev.guild_id, user_id=ev.user_id)
	logger.info("User %d was unbanned from guild %d, removing their autoban record...", ev.user_id, ev.guild_id)
