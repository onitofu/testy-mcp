import logging

from mcp.server.fastmcp import FastMCP

from testy_mcp.prompts.templates import register as register_prompts
from testy_mcp.resources.providers import register as register_resources
from testy_mcp.tools.cases import register as register_cases
from testy_mcp.tools.export import register as register_export
from testy_mcp.tools.labels import register as register_labels
from testy_mcp.tools.plans import register as register_plans
from testy_mcp.tools.projects import register as register_projects
from testy_mcp.tools.results import register as register_results
from testy_mcp.tools.statuses import register as register_statuses
from testy_mcp.tools.suites import register as register_suites

logger = logging.getLogger("testy_mcp")

mcp = FastMCP(
    "TestY TMS",
    instructions=(
        "MCP server for TestY Test Management System. "
        "Provides tools to manage test suites, test cases, test plans, "
        "and test results. Supports bulk operations for AI-driven test generation "
        "and automated test result reporting."
    ),
)

register_projects(mcp)
register_suites(mcp)
register_cases(mcp)
register_plans(mcp)
register_results(mcp)
register_export(mcp)
register_labels(mcp)
register_statuses(mcp)
register_resources(mcp)
register_prompts(mcp)
