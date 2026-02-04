import json
# export GOOGLE_PLAY_SERVICE_ACCOUNT_JSON=/path/to/service-account.json
import os
from decimal import Decimal
from enum import Enum

import google.auth.transport.requests
import requests
from google.oauth2 import service_account


class BuildNotFoundError(Exception):
    pass


class ReleaseProductionStatus(Enum):
    STATUS_UNSPECIFIED = "statusUnspecified"
    DRAFT = "draft"
    IN_PROGRESS = "inProgress"
    HALTED = "halted"
    COMPLETED = "completed"


class RollOutPercentage(Enum):
    fivePercent = Decimal("0.05")
    twentyPercent = Decimal("0.20")
    hundredPercent = Decimal("1.00")


def is_valid_status(status):
    # Iterate through all enum members and compare their values
    return status in ReleaseProductionStatus._value2member_map_


class GooglePlayClient:
    """
    Google Play Developer API client
    """

    BASE_URL = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"
    PACKAGE_NAME = "<your.application.id>"

    STANDARD_RELEASE_NOTES = [{
        'language': 'en-GB',
        'text': '<YOUR UPDATE>'
    }]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self._generate_token}",
            "Content-Type": "application/json",
        })

    @staticmethod
    def _generate_token():
        """
        Generates a JWT token.
        """
        raw_key = os.environ.get("GOOGLE_PLAY_STORE_KEY")

        if not raw_key:
            raise ValueError("GOOGLE_PLAY_STORE_KEY not set")

        service_account_info = json.loads(raw_key)

        if service_account_info is None:
            raise ValueError("The GOOGLE_PLAY_STORE_KEY environment variable is not set")

        scopes = ["https://www.googleapis.com/auth/androidpublisher"]

        # Load the service account info
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=scopes)

        # Get the Bearer token
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)
        return credentials.token

    def generate_edit_session(self) -> str:
        """
        Creates edit session id in Google Play API
        :return: response from edit_id
        """
        print(f'Generating edit session id')
        url = f'{self.BASE_URL}/{self.PACKAGE_NAME}/edits'
        try:
            response = self.session.post(url)
            response.raise_for_status()
            edit_id = response.json().get('id')
            print(f'Edit session id: {edit_id}')
            return edit_id
        except requests.RequestException as error:
            raise ValueError(f'Error generating edit session id: {error}')

    def commit_edit_session(self, edit_id):
        """
        Creates a draft version in Google Play Developer API
        :param edit_id: the id for the session
        :return: response instance of AppEdit { "id": string, "expiryTimeSeconds": string }
        """
        url = f"{self.BASE_URL}/{self.PACKAGE_NAME}/edits/{edit_id}:commit"
        data = {}  # Request body must be empty
        try:
            resp = self.session.post(url, data=json.dumps(data))
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as error:
            raise ValueError(f'Failed to commit edit {edit_id}: {error}')

    def upload_bundle(self, edit_id):
        """
        Upload a new Android App bundle to the edit id
        :param edit_id:
        :return: response instance of Bundle { "versionCode": integer, "sha1": string, "sha256": string}
        """
        data = {}
        url = f'{self.BASE_URL}/{self.PACKAGE_NAME}/edits/{edit_id}/bundles'
        try:
            resp = self.session.post(url, data=json.dumps(data))
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as error:
            raise ValueError(f'Failed to upload bundle {edit_id}: {error}')

    def patch_track(self, edit_id, version_code, status: ReleaseProductionStatus, release_notes=None,
                    roll_out_percentage: RollOutPercentage = None):
        """
        Update only the values specified and leaves the rest of the existing config data on the track unchanged
        :param edit_id:
        :param version_code:
        :param status:
        :param release_notes:
        :param roll_out_percentage:
        :return:
        """
        data = {
            'track': 'production',
            'release': [{
                'status': status,
                'versionCode': [version_code]
            }]
        }

        if release_notes is None:
            release_notes = self.STANDARD_RELEASE_NOTES
            data['release'][0]['releaseNotes'] = release_notes
        else:
            data['release'][0]['releaseNotes'] = release_notes

        if status == ReleaseProductionStatus.IN_PROGRESS.value[0] and roll_out_percentage is not None:
            data['release'][0]['userFraction'] = str(roll_out_percentage)

        ulr = f'{self.BASE_URL}/{self.PACKAGE_NAME}/edits/{edit_id}/tracks/production'

        try:
            resp = self.session.patch(ulr, data=json.dumps(data))
            resp.raise_for_status()
            return resp
        except requests.RequestException as error:
            raise ValueError(f'Failed to patch track {edit_id}: {error}')

    def get_track(self, edit_id):
        """
        Check the status of a specific track
        :param edit_id:
        :return: The response body contains an instance of Track
        """
        url = f'{self.BASE_URL}/{self.PACKAGE_NAME}/edits/{edit_id}/tracks/production'
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise ValueError(f'An error occurred getting the status of production:\n {error}')

    def get_bundles_list(self, edit_id):
        """
        Retrieves array of Android build_numbers from Google Play Developer API
        :param edit_id: T
        :return: Array of bundles [{'version': <build_number}...]
        """
        url = f'{self.BASE_URL}/{self.PACKAGE_NAME}/edits/{edit_id}/bundles'
        try:
            response = requests.get(url)
            response.raise_for_status()
            body = response.json()
            bundles = body['bundles']
            for bundle in bundles:
                print(bundle)
            return bundles
        except requests.RequestException as error:
            raise ValueError(f'An error occurred fetching the build_numbers:\n {error}')

    def get_build_number(self, edit_id, build_number):
        """
        Finds Android build_number from Google Play Developer API
        :param edit_id:
        :param build_number: The build_number to match
        :return:
        """
        builds = self.get_bundles_list(edit_id)
        match = [build for build in builds if build['versionCode'] == int(build_number)]
        if not match:
            raise BuildNotFoundError(f'There is not match for build number:\n {build_number}')
        return match

    def get_release_status_production_track(self, edit_id):
        """
        Get release status production track from Google Play Developer API
        :param edit_id:
        :return: Array of Release
        """
        url = f'{self.BASE_URL}/{self.PACKAGE_NAME}/edits/{edit_id}/tracks/production'
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise ValueError(f'An error occurred fetching the production track builds:\n {error}')

