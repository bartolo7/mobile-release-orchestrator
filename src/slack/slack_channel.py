from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SlackChannel:
    name: str
    channel: str
    webhook: Optional[str] = None

APP_RELEASE = SlackChannel(
    name="app-release",
    channel="#app-release"
)

MOBILE = SlackChannel(
    name="mobile",
    channel="#mobile-engineering"
)