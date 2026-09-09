# Import standard packages
from abc import ABC
from typing import Any

# Import LangChain packages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_parallel import ParallelSearchTool, ParallelExtractTool, ParallelTaskRunTool
from langgraph.prebuilt import create_react_agent

# Import custom modules
from src.raphael.agentry.config import config
from src.raphael.agentry.parallel.models import (
    ParallelAgentType,
    ParallelSearchRequest,
    ParallelExtractRequest,
    PersonDossier,
)

class ParallelAbstractAgent(ABC):
    """
    Models a generic agent specializing in using Parallel.
    """

    # This agent comes with pre-configured tools

    def __init__(self, system_prompt: str, type: ParallelAgentType):
        """
        Initializes a standalone Parallel sub-agent specializing in
        either simple searches, extracting webpages, or deep research.
        """
        # Define this class's state variables
        self.system_prompt = system_prompt
        self.type = type

        # Initialize the LLM (GCP creds are picked up automatically via ADC)
        # temperature=0 -- this agent's job (decide what to search, then
        # summarize findings) should be as repeatable as the underlying
        # search results allow; default sampling was an extra, controllable
        # source of run-to-run variance on top of that.
        self.model = ChatGoogleGenerativeAI(
            model=config.MODEL_ID,
            vertexai=True,
            project=config.GOOGLE_CLOUD_PROJECT,
            location=config.GOOGLE_CLOUD_LOCATION,
            temperature=0,
        )

        # Configure specialized parallel tools
        if self.type == ParallelAgentType.SEARCH:
            self.tools = [ParallelSearchTool()]
        elif self.type == ParallelAgentType.EXTRACT:
            self.tools = [ParallelExtractTool()]
        elif self.type == ParallelAgentType.RESEARCH:
            self.tools = [ParallelTaskRunTool(processor="pro-fast", task_output_schema=PersonDossier)]
        else:
            self.tools = [ParallelSearchTool()]


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
