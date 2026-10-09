"""MCP server exposing Suunto analysis tools."""

from mcp.server import MCPServer

from mcpSuunto.mcp import tools

mcp = MCPServer("Suunto")

for function in (
    tools.list_activities,
    tools.get_activity,
    tools.search_activities,
    tools.get_training_history,
    tools.get_training_load,
    tools.get_performance_trends,
    tools.get_intervals,
    tools.query_activity_records,
    tools.compare_activities,
    tools.compare_intervals,
    tools.get_similar_activities,
    tools.get_personal_bests,
    tools.get_recent_training_context,
):
    mcp.tool()(function)


def main() -> None:
    """Run the MCP server over stdio for Claude and MCP Inspector."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
