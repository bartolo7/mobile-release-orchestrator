

DIVIDER_BLOCK = {
    "type": "divider"
}


def markdown_block(text: str) -> dict:
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": text
        }
    }