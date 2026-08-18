# Import standard packages
from abc import ABC
from typing import Any

# Import LangChain packages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_parallel import ParallelSearchTool, ParallelExtractTool
from langgraph.prebuilt import create_react_agent

# Import custom modules
from src.raphael.agentry.config import config
from src.raphael.agentry.parallel.models import (
    ParallelAgentType,
    ParallelSearchRequest,
    ParallelExtractRequest,
)

class ParallelAbstractAgent(ABC):
    """
    Models a generic agent specializing in using Parallel.
    """

    # This agent comes with pre-configured tools

    def __init__(self, system_prompt: str, type: ParallelAgentType):
        """
        Initializes a standalone Parallel sub-agent specializing in
        either simple searches or extracting webpages.
        """
        # Define this class's state variables
        self.system_prompt = system_prompt
        self.type = type

        # Initialize the LLM (GCP creds are picked up automatically via ADC)
        self.model = ChatGoogleGenerativeAI(
            model=config.MODEL_ID,
            vertexai=True,
            project=config.GOOGLE_CLOUD_PROJECT,
            location=config.GOOGLE_CLOUD_LOCATION,
        )

        # Configure specialized parallel tools
        self.tools = [
            ParallelSearchTool() if self.type == ParallelAgentType.SEARCH else
            ParallelExtractTool()
        ]

        # Create the agent executor using LangGraph
        self.agent = create_react_agent(
            model=self.model,
            tools=self.tools,
            prompt=self.system_prompt,
        )

        return

    def invoke(self, query: str, **kwargs: Any) -> str:
        """
        Synchronously executes the Parallel agent for a given input query.
        """
        
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            **kwargs,
        )
        
        return result["messages"][-1].content

    async def ainvoke(self, query: str, **kwargs: Any) -> str:
        """
        Asynchronously executes the Parallel agent for a given input query.
        """
        
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": query}]},
            **kwargs,
        )
        
        return result["messages"][-1].content
