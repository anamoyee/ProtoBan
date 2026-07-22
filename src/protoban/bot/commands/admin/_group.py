from ...bot import ACL
from ...hooks.permissions import archook__only_administrators

slash_group = ACL.include_slash_group(
	"admin",
	"Configure the bot or view admin-required information.",
	# default_permissions=hikari.Permissions.ADMINISTRATOR, # we COULD do that, or we could just keep the MEGU_BUTTON >:3
)

slash_group.add_hook(archook__only_administrators)
