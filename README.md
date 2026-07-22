# ProtoBan

Automatically bans discord users when they leave the server.

### todo
- [x] ACTUALLY TEST IF IT WORKS: make it on not ban on kick
- [x] testing
  - [x] test /configure command
  - [x] test if kick doesnt ban
  - [x] test if error handler works (spread some 1/0 around the place)
    - [x] in commands
    - [x] in events
  - [x] make sure logging to Discord works (bc niver'll eat me if not)
    - [x] remove the wanky logging shit and simply make a `discord_log(guild_id, hikari.Embed(...))`
  - [x] setup rich.logging
- [x] /admin stats
  - [x] (the command impl itself, and its embed)
  - [x] count bans in a `Data__` file (user IDs of targets)
- [ ] Add AGPL License
- [ ] remove this todo from

## Usage
Install `uv` python package manager (through your distro's package manager or `pipx` or [Astral's (uv's authors) script](https://docs.astral.sh/uv/getting-started/installation/), (descending order of recommendation)), then:

> `./run.sh`

by default `dev` environment is used, **(NOTE: `"- Testmode"` markers and a few developer-oriented features (which probably shouldn't be visible to a user) will be enabled in dev mode, for production use `prod` mode)**

> **`./run.sh prod`**

select environment with the first positional argument

> `./run.sh dev --version`

any further arguments are passed to the script (note that due to how the `run.sh` script works, you have to supply at least ANYTHING as the environment (first positonal argument) to be able to pass arguments to the cli script handler (e.g. `--help`, `--version`, etc.))

Note that the above require the use of `pass` password manager with the bot token at the following path, If you wish to override the token (with your own password manager's cli/a file on disk/pasted from clipboard), use the following env variable:
`OVERRIDE_TOKEN="your_token"`
(e.g. `OVERRIDE_TOKEN=... ./run.sh prod`)
