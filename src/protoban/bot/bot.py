import os

import arc
import hikari
from hikari import GatewayBot, Intents

from ..environment import testmode

BOT = GatewayBot(
	token=os.environ["BOT_TOKEN"],  # guaranteed to exist by cli.py
	intents=Intents.ALL_UNPRIVILEGED | Intents.GUILD_MEMBERS,
	logs=None,  # already set up in cli.py
	banner=None,  # already printed in cli.py
)

ACL = arc.GatewayClient(
	BOT,
	default_enabled_guilds=(
		[
			1145433323594842166,
		]
		if testmode()
		else hikari.UNDEFINED
	),
)
