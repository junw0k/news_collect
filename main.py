from fastmcp import FastMCP
from config import settings
from tools.data_tools import register_data_tools

mcp = FastMCP("My Server")
register_data_tools(mcp, settings)

if __name__ == "__main__":
    mcp.run()