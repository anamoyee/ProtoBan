#!/usr/bin/env bash

# Usage:
#   ./run.sh [environment: str = 'dev'] ['cli.py' *args, **kwargs...]

if command -v tput >/dev/null 2>&1; then
	C_RED=$(tput setaf 1)
	C_BLUE=$(tput setaf 4)

	C_RESET=$(tput sgr0)
fi

cd "$(dirname "${BASH_SOURCE[0]}")" || {
	echo "${C_RED}Error:${C_RESET} Failed to change directory to script dir"
	exit 1
}

if ! command -v uv >/dev/null 2>&1; then
	echo "${C_RED}Error:${C_RESET} 'uv' command not found. Please install uv (via package manager, pipx or https://github.com/astral-sh/uv)"
	exit 1
fi

environment="${1:-dev}"
shift
echo "${C_BLUE}Info:${C_RESET} Running in '${environment}' environment"

if [[ -v OVERRIDE_TOKEN ]]; then
	bot_token="${OVERRIDE_TOKEN}"
else
	bot_token=$(pass "discord_tokens/${environment}/ProtoBan")
	if [[ $? -ne 0 ]]; then
		echo "${C_RED}Error:${C_RESET} Failed to retrieve token from pass"
		exit 1
	fi
fi

uv sync
if [[ $? -ne 0 ]]; then
	echo "${C_RED}Error:${C_RESET} Failed to uv sync"
	exit 1
fi

BOT_ENVIRONMENT="${environment}" BOT_TOKEN="${bot_token}" ./.venv/bin/python -OO ./.venv/bin/protoban "$@"
