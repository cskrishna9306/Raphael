# Import standard packages
import os
from dotenv import load_dotenv


class Config:
    """
    Env-driven settings for the ClickHouse client.
    """

    def __init__(self):
        """
        Initialize the settings for the ClickHouse client.
        """

        # Load the .env file
        load_dotenv()

        # Below are the settings needed to connect w/ the MCP server
        self.CLICKHOUSE_USERNAME: str = os.getenv("CLICKHOUSE_USERNAME")
        self.CLICKHOUSE_PASSWORD: str = os.getenv("CLICKHOUSE_PASSWORD")
        self.CLICKHOUSE_HOST: str = os.getenv("CLICKHOUSE_HOST")
        self.CLICKHOUSE_PORT: str = str(os.getenv("CLICKHOUSE_PORT"))

        return


config = Config()
