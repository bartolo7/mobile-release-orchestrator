import argparse
import sys

from src.clients.jira import Jira
from src.clients.utils.logging_config import setup_logger
from src.clients.utils.versions import create_app_version
from src.clients.utils.constants import MOBILE_PLATFORMS

logger = setup_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a new App version in Jira Project"
    )
    parser.add_argument(
        "platform",
        choices=MOBILE_PLATFORMS,
        help="Target platform"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the creation without calling JIRA"
    )
    return parser.parse_args()

def create_version(platform: str, dry_run:bool) -> None:

    version = create_app_version(platform)

    if dry_run:
        logger.info(
            "[DRY RUN] Would create Jira version '%s' for platform '%s'",
            version['ver'],
            platform,
        )
        return

    jira = Jira()

    logger.info(
        "Creating new App version '%s' for platform '%s' in Jira Project",
        version,
        platform,
    )

    jira.create_version(platform, version)

    logger.info("Jira version created successfully")


def main() -> int:
    logger.info("Creating App version in Jira Project")
    args = parse_args()

    try:
        create_version(args.platform, args.dry_run)
        return 0
    except ValueError as error:
        logger.error(error)
        return 1
    except Exception:
        logger.exception("Unexpected error while creating Jira version")
        return 2

if __name__ == "__main__":
    sys.exit(main())