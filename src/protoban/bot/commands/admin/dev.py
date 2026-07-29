from ....environment import testmode

if testmode():
	import linecache
	import textwrap
	import traceback

	import aiohttp
	import hikari
	from nya_codeblock import codeblock, codeblocks_from_exception
	from nya_fmt import Formatter

	async def _async_download_file_to_str(url: str) -> str:
		"""Asynchronously downloads a file from a URL and returns its contents as a string without saving it to the disk.

		Args:
			url (str): The URL of the file to download.

		Returns:
			str: The contents of the downloaded file as a string.

		Raises:
			RuntimeError: If the download fails.
		"""
		try:
			async with aiohttp.ClientSession() as session, session.get(url) as response:
				response.raise_for_status()

				content_bytes = await response.read()

				for encoding in ("utf-8", "utf-16", "utf-8-sig", "cp1252"):
					try:
						return content_bytes.decode(encoding)
					except UnicodeDecodeError:
						continue

				return content_bytes.decode("utf-8", errors="replace")
		except aiohttp.ClientResponseError as e:
			msg = f"Failed to download file from {url=}: {e}"
			raise RuntimeError(msg) from e

	import arc

	from ._group import slash_group as __slash_group

	slash_subgroup = __slash_group.include_subgroup("dev", "Developer commands, for testing and debugging purposes.")

	@slash_subgroup.include
	@arc.slash_subcommand("run", "Run python code in the bot's process.")
	async def subcmd_admin__dev__run(
		ctx: arc.GatewayContext,
		*,
		code: arc.Option[str | None, arc.StrParams("The python code to run")] = None,
		file: arc.Option[hikari.Attachment | None, arc.AttachmentParams("A file containing the python code to run")] = None,
		ephemeral: arc.Option[bool, arc.BoolParams("Hide the message?")] = True,
	):
		if file is not None:
			file_content = await _async_download_file_to_str(file.url)

		def wrap_in_async_fn(__s: str, /) -> str:
			return "async def __ex():\n" + textwrap.indent("pass\n" + __s + '\nreturn "finished without return"', "\t")

		fmt = Formatter(
			no_quoteless_str=True,
		)

		source_to_exec = ""
		if file is not None:
			source_to_exec += file_content + "\n"
		if code:
			source_to_exec += code

		ephemeral_flags = hikari.MessageFlag.EPHEMERAL if ephemeral else hikari.MessageFlag.NONE

		exec_scope = {**globals(), **locals()}

		wrapped_source = wrap_in_async_fn(source_to_exec)

		fake_filename = f"<{" ".join(subcmd_admin__dev__run.qualified_name)}>"

		linecache.cache[fake_filename] = (
			len(wrapped_source),
			None,
			wrapped_source.splitlines(keepends=True),
			fake_filename,
		)

		try:
			compiled = compile(wrapped_source, fake_filename, "exec")
		except SyntaxError as e:
			if e.filename == fake_filename and e.text is None and e.lineno is not None:
				lines = wrapped_source.splitlines(keepends=True)
				if 0 < e.lineno <= len(lines):
					e.text = lines[e.lineno - 1]

			# format_exception_only formats just the SyntaxError itself (filename, line, snippet, and caret)
			formatted_err = "".join(traceback.format_exception_only(type(e), e))
			await ctx.respond(
				codeblock(formatted_err, langcode="py"),
				flags=ephemeral_flags,
			)
			return
		except BaseException as e:
			await ctx.respond(
				codeblocks_from_exception(e),
				flags=ephemeral_flags,
			)
			return

		try:
			exec(compiled, exec_scope)

			retval: object = await exec_scope["__ex"]()
		except BaseException as e:
			await ctx.respond(
				codeblocks_from_exception(e),
				flags=ephemeral_flags,
			)
		else:
			await ctx.respond(
				codeblock(fmt(retval).plain),
				flags=ephemeral_flags,
			)
