import json
import os
from datetime import datetime
from enum import Enum
import requests
from requests.auth import HTTPBasicAuth
from .circleci import CircleCI


class Jira:
    BASE_URL = "https://<company>.atlassian.net/resp/api/3"
    ROUTES = {
        'project': '/projects',
        'issue': '/issues',
        'version': '/versions',
    }

    JIRA_PROJECT_KEY = "<PROJECT_KEY>"
    JIRA_PROJECT_ID = "<ISSUE_KEY>"

    def __init__(self):
        jira_user = os.environ.get("JIRA_USER")
        jira_token = os.environ.get("JIRA_TOKEN")
        if not jira_user or not jira_token:
            raise ValueError('JIRA_USER and JIRA_TOKEN must be set')

        self.circleci = CircleCI()
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        self.session.auth = HTTPBasicAuth(jira_user, jira_token)

    def create_version(self, platform, version_data, *, required_ci_build_data=False):
        """
        Create version or update existing version with build data
        NOTE: This is how it was implemented. The function update_ongoing_release_version did not work as expected
        :param platform:
        :param version_data:
        :param required_ci_build_data:
        :return:
        """
        build_data = {}

        if required_ci_build_data:
            build_data = self._get_ci_build_data(platform)

        url = f'{self.BASE_URL}/{self.ROUTES["version"]}'
        data = {
            "archived": False,
            "description": json.dumps(build_data),
            "name": f'{platform}-{version_data["version"]}',
            "projectId": self.JIRA_PROJECT_ID,
            "startDate": str(version_data["start_date"]),
            "releaseDate": str(version_data["release_date"]),
            "released": False
        }
        resp = requests.post(url, data=json.dumps(data))
        resp.raise_for_status()
        return resp

    def _get_ci_build_data(self, platform):
        ci_build_data = None
        pipeline_repo = f'<REPO_NAME-{platform}'
        pipelines = self.circleci.get_latest_pipelines(pipeline_repo, branch='develop')
        for pipeline in pipelines:
            workflows = self.circleci.get_workflow_from_pipeline(pipeline)
            for workflow in workflows:
                if 'test-and-distribute' in workflow['name']:
                    ci_build_data = self.circleci.get_build_data(f"workflows/{workflow['id']}")
                    break
            if ci_build_data and ci_build_data.get('prod') and ci_build_data.get('bs'):
                return ci_build_data
        return ci_build_data

    def get_all_versions(self):
        header = {"Accept": "application/json"}
        url = f'{self.BASE_URL}{self.ROUTES["project"]}/{self.JIRA_PROJECT_KEY}/versions'
        resp = self.session.get(url, headers=header)
        resp.raise_for_status()
        versions = sorted(resp.json(), key=lambda d: int(d['id']), reverse=True)
        return versions

    def update_description(self, version_id, description):
        url = f'{self.BASE_URL}{self.ROUTES['version']}/{version_id}'
        data = json.dumps({'description': json.dumps(description)})
        resp = self.session.put(url, data=data)
        resp.raise_for_status()
        return resp

    def update_version(self, version, *, released=None, archived=None, release_date=None):
        """
        Update a Jira version.
        Args:
            version: version id
            released: bool | None
            archived: bool | None
            release_date: date | None
        """
        url = f"{self.BASE_URL}{self.ROUTES['version']}/{version}"

        payload = {}
        if released is not None:
            payload["released"] = released
            if released:
                payload["releaseDate"] = (
                        release_date or datetime.today().date()
                ).isoformat()

        if archived is not None:
            payload["archived"] = archived

        if not payload:
            raise ValueError("No update fields provided")

        resp = self.session.put(url, json=payload)
        resp.raise_for_status()
        return resp

    def release_version(self, version):
        return self.update_version(version, released=True)

    def archive_version(self, version):
        return self.update_version(version, archived=True)

    def add_version_to_jira_ticket(self, jira_number, version):
        """
        Add version to jira ticket
        :param jira_number:
        :param version:
        :return:
        """
        if not version:
            raise ValueError("No version provided")

        payload = {
            'update': {
                "fixVersion": [
                    {
                        "add": {
                            "name": version,
                        }
                    }
                ]
            }
        }
        url = f'{self.BASE_URL}{self.ROUTES["issue"]}/{jira_number}'
        resp = self.session.put(url, json=payload)
        resp.raise_for_status()
        return resp

    def create_related_work(self, version_id, file_name, url):
        """
        Add file like test reports to the JIRA release version
        :param version_id:
        :param file_name:
        :param url:
        :return:
        """
        payload = {
            'category': 'Testing',
            'title': file_name,
            'url': url,
        }

        url = f'{self.BASE_URL}{self.ROUTES["version"]}/{version_id}/relatedwork'
        resp = self.session.post(url, data=json.dumps(payload))
        resp.raise_for_status()
        return resp

    def get_ongoing_release_versions(self, *, platform=None, adhoc=False):
        versions = self.get_all_versions()

        # Get all unrelease versions for iOS and Android
        unreleased_versions = list(
            filter(lambda version: not version["released"] and not version["archived"], versions))

        # Filter version by platform iOS or Android
        if platform:
            unreleased_versions = list(filter(lambda obj: platform.lower() in obj['name'], unreleased_versions))

        if not unreleased_versions:
            return None

        # If there is a hotfix 2 version in parallel will co-exist
        if adhoc:
            for version in unreleased_versions:
                if 'adhoc' in version.get("description", "").lower():
                    return version
                return None
        return unreleased_versions[0]
