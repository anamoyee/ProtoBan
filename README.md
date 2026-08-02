# ProtoBan

Automatically ban discord users when they leave the server.

## Todo

- [ ] Fix the issue with socket disconnecting after you leave the bot running
      for a while, that results in a big fat error (see `log_61.log`)
- [ ] Add `pre-commit` which will SHOW (But not fail the commit) if
      `ty` or `ruff` yell - this is there to not miss any todo comments or other
      ruff improvements
- [ ] Kick after X days of inactivity
  - [ ] Setting: how many days of inactivity
  - [ ] Setting: Exchange the kick for a ban
  - [ ] Who to exempt (which permissions - setting, in a mutli-select selectmenu
        if enough space, maybe multiple if not enoguh space)
  - [ ] Who to exempt (which roles - setting, in a multi-select select menu if
        enough space)

## Installation & Usage

1. Install source code via git: `git clone <repo url>`, if you wish to
   make changes in the future, fork this repository.

2. Install `uv` python package manager (through your distro's package manager
   or `pipx` or [Astral's (uv's authors) script][uv-docs], (descending order of
   recommendation))

3. Use the `run.sh` script.

> `./run.sh`

by default `dev` environment is used

> [!WARNING]
> `"- Testmode"` markers and a few developer-oriented features (which probably
> shouldn't be visible to a user) will be enabled in dev mode, for production
> use `prod` mode
<!--  -->
> **`./run.sh prod`**

select environment with the first positional argument

> `./run.sh dev --version`

any further arguments are passed to the script (note that due to how the `run.sh`
script works, you have to supply at least ANYTHING as the environment (first
positonal argument) to be able to pass arguments to the cli script handler
(e.g. `--help`, `--version`, etc.))

Note that the above require the use of `pass` password manager with the bot
token at the following path, If you wish to override the token (with your own
password manager's cli/a file on disk/pasted from clipboard), use
the following env variable: `OVERRIDE_TOKEN="your_token"`
(e.g. `OVERRIDE_TOKEN=... ./run.sh prod`)

[uv-docs]: https://docs.astral.sh/uv/getting-started/installation/
