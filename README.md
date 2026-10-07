# testy-mcp

MCP plugin for TestY. The `get_me` tool takes no arguments and returns the
authenticated user's `username`, `firstname` and `lastname`.
Sign in through the browser with your existing TestY account.

## Clients

Once the plugin is enabled in TestY, connect using the instructions below.
Replace `http://127.0.0.1/plugins/mcp/` with your TestY MCP endpoint URL.

### Codex CLI

```bash
codex mcp add testy --url http://127.0.0.1/plugins/mcp/
codex mcp login testy
```

### Codex Desktop

Add an HTTP MCP server with your TestY MCP endpoint URL and sign in through the
browser.

### Claude Code

```bash
claude mcp add --transport http testy http://127.0.0.1/plugins/mcp/
```

Then select authentication in `/mcp`. Login uses TestY credentials in the browser.
