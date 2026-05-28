from src.models.release import Platform

def get_platform_icon(platform: Platform) -> str:
    return "apple" if platform.value == "ios" else "robot_face"


def get_store_name(platform: Platform) -> str:
    return "App Store Connect" if platform.value == "ios" else "Google Play"