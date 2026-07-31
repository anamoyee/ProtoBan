import os

import arc
import hikari
import miru

BOT = hikari.GatewayBot(
	token=os.environ["BOT_TOKEN"],  # guaranteed by cli.py to exist
	intents=(
		hikari.Intents.ALL_UNPRIVILEGED  #
		| hikari.Intents.GUILD_MEMBERS
	),
	logs=None,  # already set up in cli.py
	banner=None,  # already printed in cli.py
)

ACL = arc.GatewayClient(
	BOT,
	default_enabled_guilds=(  # do not change conditionally based on testmode() as this duplicates command registration (global and enabled_guild commands registered in the same guild)
		1145433323594842166,
	),
)

MCL = miru.Client.from_arc(ACL)
