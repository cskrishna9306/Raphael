from typing import Optional
from parallel import AsyncParallel, Parallel

# Import custom modules
from src.raphael.agentry.parallel.models import PersonDossier
from src.raphael.parallel.config import config


class ParallelClient:
    """
    Wrapper on top of the Parallel SDK providing search and deep research capabilities.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Parallel client for both sync and async execution.
        """
        self._api_key = api_key or config.PARALLEL_API_KEY
        self._client: Optional[Parallel] = None
        self._async_client: Optional[AsyncParallel] = None

    @property
    def client(self) -> Parallel:
        if self._client is None:
            if not self._api_key:
                raise ValueError("PARALLEL_API_KEY is not set. Please add it to your .env or pass api_key.")
            self._client = Parallel(api_key=self._api_key)
        return self._client

    @property
    def async_client(self) -> AsyncParallel:
        if self._async_client is None:
            if not self._api_key:
                raise ValueError("PARALLEL_API_KEY is not set. Please add it to your .env or pass api_key.")
            self._async_client = AsyncParallel(api_key=self._api_key)
        return self._async_client


    @staticmethod
    def _build_person_research_prompt(name: str, additional_context: Optional[str] = None) -> str:
        """
        Constructs an in-depth research prompt for a cinema/television professional.
        """
        prompt = (
            f"Conduct comprehensive research on the film industry professional: '{name}'.\n"
            f"Extract detailed information including:\n"
            f"1. Biographical summary and primary roles (e.g. Actor, Director, Writer, DP).\n"
            f"2. Notable filmography / production credits with release years, roles, box office performance, "
            f"and critical reception.\n"
            f"3. Key collaborators (actors, directors, cinematographers, writers) they have worked with, "
            f"the shared projects, and qualitative chemistry/sentiment notes on their working relationships.\n"
            f"4. Personality profile, working style (e.g. method acting, auteur, collaborative), critical acclaim, "
            f"major awards, and any notable critiques or controversies.\n"
            f"5. Casting attributes including demographics, physical characteristics (build, height), "
            f"and notable screen presence traits."
        )
        if additional_context:
            prompt += f"\nAdditional Context / Specific Focus: {additional_context}"
        return prompt

    def search(
        self,
        query: str,
        processor: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """
        Synchronously run an unstructured search against the Parallel API.
        """
        proc = processor or config.PARALLEL_PROCESSOR
        t_out = timeout or config.PARALLEL_API_TIMEOUT

        try:
            task = self.client.task_run.create(
                input=query,
                processor=proc,
                timeout=t_out,
            )
            print(f"[Parallel] Task created (ID: {task.run_id}, Interaction: {task.interaction_id})")

            result = self.client.task_run.result(
                task.run_id,
                api_timeout=t_out,
            )
            return result.output.content if hasattr(result.output, "content") else str(result.output)
        except Exception as e:
            print(f"[Parallel] Error during search: {e}")
            return ""

    async def asearch(
        self,
        query: str,
        processor: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """
        Asynchronously run an unstructured search against the Parallel API.
        """
        proc = processor or config.PARALLEL_PROCESSOR
        t_out = timeout or config.PARALLEL_API_TIMEOUT

        try:
            task = await self.async_client.task_run.create(
                input=query,
                processor=proc,
                timeout=t_out,
            )
            print(f"[Parallel Async] Task created (ID: {task.run_id}, Interaction: {task.interaction_id})")

            result = await self.async_client.task_run.result(
                task.run_id,
                api_timeout=t_out,
            )
            return result.output.content if hasattr(result.output, "content") else str(result.output)
        except Exception as e:
            print(f"[Parallel Async] Error during asearch: {e}")
            return ""

    def research_person(
        self,
        name: str,
        additional_context: Optional[str] = None,
        processor: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Optional[PersonDossier]:
        """
        Synchronously executes deep research on a specific person, returning a structured PersonDossier.
        """
        proc = processor or config.PARALLEL_RESEARCH_PROCESSOR
        t_out = timeout or config.PARALLEL_API_TIMEOUT
        prompt = self._build_person_research_prompt(name, additional_context)

        try:
            print(f"[Parallel] Starting deep research on '{name}' using processor '{proc}'...")
            result = self.client.task_run.execute(
                input=prompt,
                processor=proc,
                output=PersonDossier,
                timeout=t_out,
            )
            return result.output
        except Exception as e:
            print(f"[Parallel] Error during person research on '{name}': {e}")
            return None

    async def aresearch_person(
        self,
        name: str,
        additional_context: Optional[str] = None,
        processor: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Optional[PersonDossier]:
        """
        Asynchronously executes deep research on a specific person, returning a structured PersonDossier.
        """
        proc = processor or config.PARALLEL_RESEARCH_PROCESSOR
        t_out = timeout or config.PARALLEL_API_TIMEOUT
        prompt = self._build_person_research_prompt(name, additional_context)

        try:
            print(f"[Parallel Async] Starting deep research on '{name}' using processor '{proc}'...")
            result = await self.async_client.task_run.execute(
                input=prompt,
                processor=proc,
                output=PersonDossier,
                timeout=t_out,
            )
            return result.output
        except Exception as e:
            print(f"[Parallel Async] Error during person research on '{name}': {e}")
            return None

