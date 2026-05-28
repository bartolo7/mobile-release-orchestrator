from src.models.release import Release

from src.slack.slack_blocks import (
    DIVIDER_BLOCK,
    markdown_block,
)

from src.slack.slack_templates import (
    get_platform_icon,
    get_store_name,
)


def build_release_candidate_draft_message(release:Release) -> list[dict]:

    icon = get_platform_icon(release.platform)
    store = get_store_name(release.platform)

    header = (
        f"> :{icon}: Release candidate *{release.version}* - build *{release.build_number}*. "
        f"Links: "
        f"<{release.circleci_pipeline_link} | CI build> / "
        f"<{release.jira_project_link} | JIRA project>"
    )

    draft_message = (
        f"> :information_source: The release is in *draft* status in *{store}*"
    )

    return [
        markdown_block(header),
        DIVIDER_BLOCK,
        markdown_block(draft_message),
    ]

def build_bump_android_message(
    version: str,
    roll_out: str | None = None,
    failed_bump: bool = False,
    circle_build_url: str | None = None,
) -> list[dict]:

    if failed_bump:
        message = (
            f"> :rotating_light: Roll-out update failed for "
            f":android: version *{version}* "
            f"<{circle_build_url or ''} | workflow here>"
        )
    else:
        message = (
            f"> Play Store roll-out for :android: "
            f"version *{version}* set to *{roll_out or ''}%* "
            f"- <{circle_build_url or ''} | workflow here>"
        )

    return [
        markdown_block(message),
        DIVIDER_BLOCK,
    ]