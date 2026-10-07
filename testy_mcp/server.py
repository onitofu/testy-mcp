from functools import wraps

from mcp.server.fastmcp import FastMCP

from testy_mcp.prompts.analyze_failures import AnalyzeFailuresPrompt
from testy_mcp.prompts.generate_cases import GenerateCasesPrompt
from testy_mcp.prompts.review_coverage import ReviewCoveragePrompt
from testy_mcp.resources.project_labels import ProjectLabelsResource
from testy_mcp.resources.project_overview import ProjectOverviewResource
from testy_mcp.resources.project_statuses import ProjectStatusesResource
from testy_mcp.tools.add_tests_to_plan import AddTestsToPlanTool
from testy_mcp.tools.create_case import CreateCaseTool
from testy_mcp.tools.create_cases_bulk import CreateCasesBulkTool
from testy_mcp.tools.create_label import CreateLabelTool
from testy_mcp.tools.create_plan import CreatePlanTool
from testy_mcp.tools.create_suite import CreateSuiteTool
from testy_mcp.tools.create_suites_bulk import CreateSuitesBulkTool
from testy_mcp.tools.delete_case import DeleteCaseTool
from testy_mcp.tools.delete_suite import DeleteSuiteTool
from testy_mcp.tools.export_plan_results import ExportPlanResultsTool
from testy_mcp.tools.export_suite import ExportSuiteTool
from testy_mcp.tools.get_case import GetCaseTool
from testy_mcp.tools.get_plan import GetPlanTool
from testy_mcp.tools.get_plan_statistics import GetPlanStatisticsTool
from testy_mcp.tools.get_project import GetProjectTool
from testy_mcp.tools.list_cases import ListCasesTool
from testy_mcp.tools.list_labels import ListLabelsTool
from testy_mcp.tools.list_plans import ListPlansTool
from testy_mcp.tools.list_projects import ListProjectsTool
from testy_mcp.tools.list_statuses import ListStatusesTool
from testy_mcp.tools.list_suites import ListSuitesTool
from testy_mcp.tools.list_tests import ListTestsTool
from testy_mcp.tools.submit_result import SubmitResultTool
from testy_mcp.tools.submit_results_bulk import SubmitResultsBulkTool
from testy_mcp.tools.update_case import UpdateCaseTool
from testy_mcp.tools.update_suite import UpdateSuiteTool


class TestyMcpServer:
    tool_types = (
        ListProjectsTool,
        GetProjectTool,
        ListSuitesTool,
        CreateSuiteTool,
        CreateSuitesBulkTool,
        UpdateSuiteTool,
        DeleteSuiteTool,
        ListCasesTool,
        GetCaseTool,
        CreateCaseTool,
        CreateCasesBulkTool,
        UpdateCaseTool,
        DeleteCaseTool,
        ListPlansTool,
        GetPlanTool,
        CreatePlanTool,
        AddTestsToPlanTool,
        ListTestsTool,
        SubmitResultTool,
        SubmitResultsBulkTool,
        ExportSuiteTool,
        ExportPlanResultsTool,
        ListLabelsTool,
        CreateLabelTool,
        ListStatusesTool,
        GetPlanStatisticsTool,
    )
    resource_types = (ProjectOverviewResource, ProjectLabelsResource, ProjectStatusesResource)
    prompt_types = (GenerateCasesPrompt, AnalyzeFailuresPrompt, ReviewCoveragePrompt)

    @staticmethod
    def _handler(component):
        @wraps(component.execute)
        def handler(*args, **kwargs):
            return component.execute(*args, **kwargs)

        handler.__name__ = component.name
        handler.__qualname__ = component.name
        return handler

    def build(self) -> FastMCP:
        server = FastMCP(
            "TestY TMS",
            instructions=(
                "MCP server for TestY Test Management System. "
                "Provides tools to manage test suites, test cases, test plans, "
                "and test results. Supports bulk operations for AI-driven test generation "
                "and automated test result reporting."
            ),
        )
        for tool_type in self.tool_types:
            tool = tool_type()
            server.add_tool(self._handler(tool), name=tool.name)
        for resource_type in self.resource_types:
            resource = resource_type()
            server.resource(resource.uri, name=resource.name)(self._handler(resource))
        for prompt_type in self.prompt_types:
            prompt = prompt_type()
            server.prompt(name=prompt.name)(self._handler(prompt))
        return server


mcp = TestyMcpServer().build()
