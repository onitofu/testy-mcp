# TestY MCP

[Website](https://yadro.com/ru/opensource/testy/)

MCP plugin for [TestY](https://gitlab-pub.yadro.com/testy) that lets AI clients
manage test suites, cases, plans and results. Supports bulk operations and exports
for test generation and result analysis.

## Tools

| Tool | Description |
| --- | --- |
| `get_me` | Get the authenticated user's profile. |
| `list_projects` | List projects. |
| `get_project` | Get project details and statistics. |
| `list_suites` | List test suites in a project. |
| `create_suite` | Create a test suite. |
| `create_suites_bulk` | Create multiple test suites, including nested suites. |
| `update_suite` | Update a test suite. |
| `delete_suite` | Soft-delete a test suite. |
| `list_cases` | List test cases with filters and pagination. |
| `get_case` | Get full test case content. |
| `create_case` | Create a simple or multi-step test case. |
| `create_cases_bulk` | Create multiple test cases in one transaction. |
| `update_case` | Update a test case. |
| `delete_case` | Soft-delete a test case. |
| `list_plans` | List test plans in a project. |
| `get_plan` | Get test plan details and statistics. |
| `create_plan` | Create a test plan, optionally adding test cases. |
| `add_tests_to_plan` | Add test cases to a test plan. |
| `list_tests` | List tests in a plan with their current statuses. |
| `submit_result` | Submit a test result. |
| `submit_results_bulk` | Submit multiple test results in one transaction. |
| `export_suite` | Export test cases from a suite. |
| `export_plan_results` | Export test plan results. |
| `list_labels` | List project labels. |
| `create_label` | Create a project label. |
| `list_statuses` | List system and custom result statuses. |
| `get_plan_statistics` | Get status distribution, pass rate and completion rate. |

## Server installation

Verified only with [TestY](https://gitlab-pub.yadro.com/testy) `2.2.1`, Python
`3.11.9`.

1. Add `testy-mcp` in `backend/testy/requirements/prod.in`.

   ```text
   git+https://github.com/onitofu/testy-mcp.git@v1.0.0
   ```

2. Regenerate lock files in the project's Python environment.

   ```bash
   cd backend/testy/requirements
   pip-compile prod.in
   pip-compile dev.in
   ```

3. In `nginx/testy-dev.conf.template` or `nginx/testy-prod.conf.template`, add
   `\.well-known` to the existing backend route expression alongside `plugins`.

4. Rebuild and restart.

## Clients

Replace `http://127.0.0.1/plugins/mcp/` with your
[TestY](https://gitlab-pub.yadro.com/testy) MCP endpoint URL.

### Codex CLI

```bash
codex mcp add testy --url http://127.0.0.1/plugins/mcp/
codex mcp login testy
```

### Codex Desktop

Add an HTTP MCP server with the endpoint URL and sign in through the browser.

### Claude Code

```bash
claude mcp add --transport http testy http://127.0.0.1/plugins/mcp/
```

Select authentication in `/mcp` and sign in through the browser with your
[TestY](https://gitlab-pub.yadro.com/testy) account.

Verify with `get_me`. Example:

```json
{"username":"admin","first_name":"","last_name":""}
```
