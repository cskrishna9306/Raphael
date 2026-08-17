# Import standard packages
import os
from contextlib import AsyncExitStack


# Import MCP packages
from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

# Import custom packages
from src.raphael.clickhouse.config import config


class ClickHouseClient:
    """
    Object responsible for setting up the ClickHouse MCP client.
    
    This class is NOT responsible for making any LLM/agent calls (anti-goals),
    rather we only provide an interface for an agentic framework to invoke
    ClickHouse APIs via this class.
    """

    def __init__(self):
        """
        Initialize the connection w/ the ClickHouse MCP server.
        """
        
        self.server_params = StdioServerParameters(
            command="uv",
            args=[
                "run",
                "--with", "mcp-clickhouse",
                "mcp-clickhouse"
            ],
            env={
                "CLICKHOUSE_HOST": config.CLICKHOUSE_HOST,
                "CLICKHOUSE_PORT": config.CLICKHOUSE_PORT,   
                "CLICKHOUSE_USER": config.CLICKHOUSE_USERNAME,
                "CLICKHOUSE_PASSWORD": config.CLICKHOUSE_PASSWORD,
                "CLICKHOUSE_SECURE": "true",
                **os.environ # Continues to carry your GOOGLE_API_KEY to Gemini
            }
        )

        return

    async def __aenter__(self):
        """
        Start the ClickHouse MCP subprocess and session, then load tools.
        The session is kept alive until __aexit__ is called.
        """
        self._stack = AsyncExitStack()
        await self._stack.__aenter__()

        read_stream, write_stream = await self._stack.enter_async_context(
            stdio_client(self.server_params)
        )
        self.session = await self._stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

        await self.session.initialize()
        self.tools = await load_mcp_tools(self.session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Tear down the MCP session and subprocess cleanly.
        """
        await self._stack.__aexit__(exc_type, exc_val, exc_tb)
