import os
import json
import jwt
from time import time, mktime
from datetime import datetime, timedelta
import requests


class AppStoreConnectClient:
    BASE_URL = 'https://appstoreconnect.appspot.com/v1'
    APP_ID = '<Apple-assigned APP Store identifier located in APP Information in App Store Connect>'
    RELEASE_NOTES = {'en-GB': '', 'sv': ''}

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self._generate_jwt}',
            'Content-Type': 'application/json'
        })

    @staticmethod
    def _generate_jwt() -> str:
        """
        Generates a JWT token for App Store Connect.
        """
        dt = datetime.now() + timedelta(milliseconds=10)

        # 1 Generate APPSTORE_CONNECT_AUTH => User and Access => Generate API Key
        # 2 kid (Key ID). After generating the key, App Store Connect shows a Key ID (example T39Z6JDMJA)
        # 3 iss (Issuer ID). App Store Connect => User  and Access => Keys => View Issuer ID

        headers = {
            'alg': 'ES256',
            'kid': os.environ.get('APPSTORECONNECT_APP_ID', '<KID VALUE>'),
            'typ': 'JWT',
        }

        payload = {
            'iss': os.environ.get('APPSTORECONNECT_CONNECT_ISSUER_ID', '<ISSUER ID VALUE>'),
            'iat': int(time()),
            'exp': int(mktime(dt.timetuple())),
            'aud': 'appstoreconnect-v1',
        }

        signing_key = os.environ.get('APPSTORE_CONNECT_AUTH', '').replace('\\n', '\n')

        if not signing_key:
            raise ValueError("Missing 'APPSTORE_CONNECT_AUTH' environment variable")

        token = jwt.encode(payload, signing_key, algorithm='ES256', headers=headers)

        return token

    def get_all_version(self):
        """
        List all versions of App Store Connect.
        """
        params = {'limit': 5}

        url = f'{self.BASE_URL}/apps/{self.APP_ID}/appStoreVersions'

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise ValueError(f'Error getting App Store Versions: {error}')

    def create_version(self, version, release_type):
        """
        Creates a version on App Store Connect
        :param release_type:
        :param version: the version number
        :return: response from api
        """
        url = f'{self.BASE_URL}/appStoreVersions'

        data = {
            'data': {
                'type': 'appStoreVersion',
                'attributes': {
                    'platform': 'IOS',
                    'versionString': version,
                    'releaseType': release_type
                },
                'relationships': {
                    'app': {
                        'data': {
                            'id': self.APP_ID,
                            'type': 'apps'
                        }
                    }
                }
            }
        }

        try:
            response = self.session.post(url, data=json.dumps(data))
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise ValueError(f'Error creating a new version in AppStoreConnect: {error}')

    def update_version(self, version_id, build_id, version_number=None):
        """
        Update a version on App Store Connect
        """
        url = f'{self.BASE_URL}/appStoreVersions/{version_id}'
        data = {
            'data': {
                'id': version_id,
                'type': 'appStoreVersions',
                'relationships': {
                    'build': {
                        'data': {
                            'id': build_id,
                            'type': 'builds'
                        }
                    }
                }
            }
        }

        if version_number:
            data['data']['attributes'] = {
                'versionString': version_number
            }

        try:
            response = self.session.patch(url, data=json.dumps(data))
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise ValueError(f'Error updating App Store Version: {error}')

    def list_version(self, version_string):
        """
        List all versions of App Store Connect matching the version string
        """
        url = f'{self.BASE_URL}/apps/{self.APP_ID}/appStoreVersions?filter[versionString]={version_string}'
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise ValueError(f'Error listing App Store Versions: {error}')

    def get_builds(self):
        """
        List all Builds on App Store Connect available for use
        """
        try:
            response = self.session.get(f'{self.BASE_URL}/builds')
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise ValueError(f'Error listing App Store Builds: {error}')

    def list_version_localizations(self, version_id):
        """
        List all Localization Instances for the App Version
        """
        try:
            response = self.session.get(
                f'{self.BASE_URL}/appStoreVersions/{version_id}/appStoreVersionLocalizations'
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise ValueError(f'Error listing App Store Version Localizations: {error}')

    def get_latest_whats_new(self):
        """
        Return "What´s New in This Version" in the latest release version
        """
        release_notes = self.RELEASE_NOTES.copy()
        release_versions = self.get_all_version()

        filter_versions = [version for version in release_versions['data'] if
                           version['attributes']['appVersionState'] == 'READY_FOR_DISTRIBUTION']

        # There are two localizations in each release version: en-GB and sv
        localizations = self.list_version_localizations(filter_versions[0]['id'])

        for localization in localizations['data']:
            release_notes[localization['attributes']['locale']] = localization['attributes']['whatsNew']

        return release_notes

    def create_phased_release_version(self, version_id):
        """
        Creates a phased release plan for the app version
        """
        data = {
            'data': {
                'type': 'appStoreVersionPhasedRelease',
                'attributes': {
                    'phasedReleaseState': 'INACTIVE'
                },
                'relationships': {
                    'appStoreVersion': {
                        'data': {
                            'id': version_id,
                            'type': 'appStoreVersions'
                        }
                    }
                }
            }
        }

        try:
            response = self.session.post(
                f'{self.BASE_URL}/appStoreVersionPhasedReleases',
                data=json.dumps(data)
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise ValueError(f'Error creating a new phased release version: {error}')

    def update_localization_whats_new(self, loc_id, whats_new_text):
        """
        Update Localization Instances for the App versoin
        :param loc_id: the id of the localization instance
        """
        data = {
            'data': {
                'id': loc_id,
                'type': 'appStoreVersionLocalizations',
                'attributes': {
                    'whatsNew': whats_new_text
                }
            }
        }

        try:
            response = self.session.patch(
                f'{self.BASE_URL}/appStoreVersionLocalizations/{loc_id}',
                data=json.dumps(data)
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise ValueError(f'Error updating App Store Localization Localizations: {error}')

    def create_review(self):
        """
        Submits the App for Review
        """
        data = {
            'data': {
                'type': 'reviewSubmission',
                'attributes': {
                    'platform': 'IOS',
                },
                'relationships': {
                    'app': {
                        'id': self.APP_ID,
                        'type': 'apps'
                    }
                }
            }
        }

        try:
            response = self.session.post(
                f'{self.BASE_URL}/reviewSubmissions',
                data=json.dumps(data)
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise ValueError(f'Error creating app for review: {error}')

    def list_reviews(self):
        """
        List Phased Release Plan for the App Version
        """
        try:
            response = self.session.get(
                f'{self.BASE_URL}/reviewSubmissions?filter[app]={self.APP_ID}')
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise ValueError(f'Error getting list of reviews for the App: {error}')

    def add_app_version_for_review(self, review_id, version_id):
        """
        Adds the App Store Version for review
        :param review_id: The ID of the Review created for the App
        :param version_id
        """
        data = {
            'data': {
                'type': 'reviewSubmissionItems',
                'relationships': {
                    'appStoreVersion': {
                        'data': {
                            'id': version_id,
                            'type': 'appStoreVersions'
                        }
                    },
                    'reviewSubmission': {
                        'data': {
                            'id': review_id,
                            'type': 'reviewSubmissions'
                        }
                    }
                }
            }
        }

        try:
            response = self.session.post(
                f'{self.BASE_URL}/reviewSubmissionItems',
                data=json.dumps(data)
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise ValueError(f'Error adding app version for review: {error}')

    def submit_review(self, review_id):
        """
        Adds the App Store Version for review
        """
        data = {
            'data': {
                'id': review_id,
                'type': 'reviewSubmissions',
                'attributes': {
                    'submitted': True
                }
            }
        }

        try:
            response = self.session.patch(
                f'{self.BASE_URL}/reviewSubmissions/{review_id}',
                data=json.dumps(data))
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise ValueError(f'Error submitting app for review: {error}')

    def get_app_status(self, version_id):
        """
        Get the App Store Status for a specific version
        """
        try:
            response = self.session.get(
                f'{self.BASE_URL}/appStoreVersion/{version_id}',
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise ValueError(f'Error getting App Store Status for version: {version_id}')

    def release_app(self, version_id):
        """
        Release the App version to production
        """
        data = {
            'data': {
                'type': 'appStoreVersionReleaseRequests',
                'relationships': {
                    'appStoreVersion': {
                        'data': {
                            'type': 'appStoreVersions',
                            'id': version_id
                        }
                    }
                }

            }
        }

        try:
            response = self.session.post(
                f'{self.BASE_URL}/appStoreVersionReleaseRequests',
                data=json.dumps(data)
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise ValueError(f'Error releasing app version to production: {version_id}')

    def ensure_phased_release_for_version(self, version_id: str) -> str:
        """
        Ensure this appStoreVersion has phased release enabled
        Returns: "EXISTS" or "CREATED"
        """
        response = self.create_phased_release_version(version_id)
        if response.status_code == 409:
            print(f"App Store Version {version_id} phased release already exists")
            return "EXISTS"
        response.raise_for_status()
        return "CREATED"
