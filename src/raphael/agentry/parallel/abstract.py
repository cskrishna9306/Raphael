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

class _TurboParallelSearchTool(ParallelSearchTool):
    """
    ParallelSearchTool with `mode` pinned to "turbo", regardless of what the
    LLM's tool call requests.

    casting_director, risk_management, and enrichment's PersonSearchAgent all
    use this for single-hop "does this real person/fact match" lookups, not
    the multi-hop background research the pricier tiers are meant for -- and
    left unset, the search API defaults to "advanced". "basic" and
    "advanced" are priced identically ($5/1000 requests); "turbo" is 5x
    cheaper ($1/1000). Parallel's pricing page also lists a "fast" tier at
    the same price, but the installed langchain-parallel SDK's `mode` enum
    only accepts "turbo"/"basic"/"advanced" -- "fast" is a removed legacy
    value the SDK now remaps to "basic" (confirmed by hitting exactly that
    ValueError), so "turbo" is the actual reachable cheap tier here, not a
    stand-in for it. See https://parallel.ai/pricing. Forced here rather
    than left to the model's tool-call discretion so the saving is
    guaranteed, not just likely.
    """

    async def _arun(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        kwargs["mode"] = "turbo"
        return await super()._arun(*args, **kwargs)

    def _run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        kwargs["mode"] = "turbo"
        return super()._run(*args, **kwargs)


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
            timeout=config.LLM_TIMEOUT_SECONDS,
            max_retries=config.LLM_MAX_RETRIES,
        )

        # Configure specialized parallel tools
        if self.type == ParallelAgentType.SEARCH:
            self.tools = [_TurboParallelSearchTool()]
        elif self.type == ParallelAgentType.EXTRACT:
            self.tools = [ParallelExtractTool()]
        elif self.type == ParallelAgentType.RESEARCH:
            self.tools = [ParallelTaskRunTool(processor="pro-fast", task_output_schema=PersonDossier)]
        else:
            self.tools = [_TurboParallelSearchTool()]


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
