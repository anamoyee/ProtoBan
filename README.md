# ProtoBan

Automatically ban discord users when they leave the server.

## Todo
- [ ] Fix the issue with socket disconnecting that results in a big fat error (see `log_61.log`)

## Installation & Usage
1. Install source code via git: `git clone <repo url>`, if you wish to make changes in the future, fork this repository.

2. Install `uv` python package manager (through your distro's package manager or `pipx` or [Astral's (uv's authors) script](https://docs.astral.sh/uv/getting-started/installation/), (descending order of recommendation)), then:

3. Use the `run.sh` script.

> `./run.sh`

by default `dev` environment is used, **(NOTE: `"- Testmode"` markers and a few developer-oriented features (which probably shouldn't be visible to a user) will be enabled in dev mode, for production use `prod` mode)**

> **`./run.sh prod`**

select environment with the first positional argument

> `./run.sh dev --version`

any further arguments are passed to the script (note that due to how the `run.sh` script works, you have to supply at least ANYTHING as the environment (first positonal argument) to be able to pass arguments to the cli script handler (e.g. `--help`, `--version`, etc.))

Note that the above require the use of `pass` password manager with the bot token at the following path, If you wish to override the token (with your own password manager's cli/a file on disk/pasted from clipboard), use the following env variable:
`OVERRIDE_TOKEN="your_token"`
(e.g. `OVERRIDE_TOKEN=... ./run.sh prod`)
