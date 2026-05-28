import os
import ssl
import certifi
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from src.config.logging_config import setup_logger

logger = setup_logger(__name__)

class SlackClient:

    def __init__(self, token: str | None = None):
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        if not self.token:
            raise ValueError("SLACK_BOT_TOKEN environment variable not set")

        ssl_context = ssl.create_default_context(cafile=certifi.where())

        self.client = WebClient(token=self.token, ssl=ssl_context)

    def healthcheck(self) -> bool:
        resp = self._safe_slack_call(
            self.client.auth_test
        )
        return resp["ok"]

    def send_blocks(
            self,
            channel: str,
            blocks: list,
            thread_ts: str | None = None,
            reply_broadcast: bool = False,
    ):
        kwargs = {
            "channel": channel,
            "blocks": blocks,
            "text": "New notification from Release Orchestrator"
        }

        if thread_ts:
            kwargs["thread_ts"] = thread_ts

            if reply_broadcast:
                kwargs["reply_broadcast"] = True


        return self._safe_slack_call(
            self.client.chat_postMessage,
            **kwargs)

    def _safe_slack_call(self, operation, **kwargs):
        """
        Execute a Slack SDK operation safely with consistent
        logging and error handling.
        """

        try:
            response = operation(**kwargs)

            logger.info(
                "Slack API call succeeded: %s",
                operation.__name__,
            )

            return response

        except SlackApiError as error:
            logger.error(
                "Slack API error during %s: %s",
                operation.__name__,
                error.response["error"],
            )

            raise

        except Exception:
            logger.exception(
                "Unexpected error during Slack operation: %s",
                operation.__name__,
            )

            raise