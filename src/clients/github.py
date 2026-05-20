import os
import requests


class Github:
    BASE_URL = 'https://api.github.com/repos'
    ENTITY = "<COMPANY_NAME>"
    TAGS = []

    def __init__(self):
        self.token = os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "Authorization": f"token {self.token}"
        })

    def _get(self, url):
        return self.session.get(url, verify=False)

    def clear_tags(self):
        self.TAGS = []

    def get_app_changelog(self, platform, prev_release_tag, new_tag):
        """
        Gets the change log between 2 tags
        :param platform:
        :param prev_release_tag:
        :param new_tag:
        :return: A list of changes
        """
        print(f'Getting changelog for {platform} between {prev_release_tag} and {new_tag}')
        pre_tag = self.get_tag(platform, prev_release_tag)
        new_tag = self.get_tag(platform, new_tag)
        url = f'{self.BASE_URL}/{self.ENTITY}/{repo['apps'][platform.lower()]}/compare/{prev_release_tag}...{new_tag}'
        resp = self._get(url)
        return self.format_commits(resp.json()['commits'])

    def format_commits(self, commits):
        changes = []
        for commit in commits:
            commit_heading = f" #### {commit['commit']['committer']['date']}"
            commit_author = f" Author: {commit['commit']['author']['name']}"
            commit_message = f" {commit['commit']['message']}"
            commit_text = f" {commit_heading}\n{commit_author}\n{commit_message}"
            changes.append(commit_text)
        return '\n\n\n\n'.join(changes)

    def get_tag(self, platform, tag):
        if not self.TAGS:
            self.get_tag_list(platform)
        for tag in self.TAGS:
            if f'{tag}' in tag['ref']:
                return tag['ref'].split('/')[-1]
        return None

    def get_tag_list(self, platform):
        url = f'{self.BASE_URL}/{self.ENTITY}/{'<REPO>'}/git/refs/tags'
        resp = self._get(url)
        if resp.status_code == 200:
            for tag in resp.json():
                self.TAGS.append(tag)


    def get_pr_desc(self, repo_name=None, pr_number=None):
        """
        This function fetches the PR description from the GitHub API.
        :param repo_name:
        :param pr_number:
        :return:
        """
        if not repo_name or not pr_number:
            pr_link = os.environ.get("CIRCLE_PR_NUMBER")
            if pr_link:
                repo_name = pr_link.split('/')[-3]
                pr_number = pr_link.split('/')[-1]
            else:
                raise Exception("PR number not found in environment variable")
        url = f'{self.BASE_URL}/{self.ENTITY}/{repo_name}/pulls/{pr_number}'
        resp = self._get(url).json()
        return resp['body']

