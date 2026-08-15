# Import Parallel SDK
from parallel import Parallel

# Import custom modules
from src.raphael.parallel.config import config


class ParallelClient:
    """
    Wrapper on top of the Parallel SDK.
    """

    def __init__(self):
        """
        Initialize the Parallel client.
        """

        # NOTE: Place error-handling blocks
        
        # The client itself (synchronous)
        self.client = Parallel(api_key=config.PARALLEL_API_KEY)

        # NOTE: Asynchronous usage requires a different object creation

        return

    # Let's create wrappers over both the sync and async functionality!
    # Use case for the async functionality would be to not wait for a response
    # from the Parallel API and continue working on other tasks
    # Maybe run multiple searches in parallel!

    def search(self, query: str, processor: str | None = config.PARALLEL_PROCESSOR) -> str:
        """
        Routine to search a simple query against the Parallel API.
        """
        try:
            # Actually invoke Parallel API
            task = self.client.task_run.create(
                input=query,
                # processor determines the effort behind the search
                # "base" is a balanced search amongst lite, core, pro, and ultra
                processor=processor,
            )

            # Log to console the request ID
            print(f"Interaction ID: {task.interaction_id}")

            # The below call is blocking, and will timeout after 1min
            result = self.client.task_run.result(
                task.run_id,
                api_timeout=config.PARALLEL_API_TIMEOUT
            )

            return result.output.content

        except Exception as e:
            # Brain-dead simple error-handling of all time
            print(f"Error: Ran into an error while searching against Parallel: {e}")

        return ""
