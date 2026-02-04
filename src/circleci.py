import json
import re
import os
import requests


class CircleCI:
    KEY_TOKEN = None
    BASE_URL_V1 = 'https://circleci.com/api/v1.1'
    BASE_URL_V2 = 'https://circleci.com/api/v2'
    PROJECT_ROUTE = 'projects/gh'
    PROJECT_V1_ROUTE = 'projects/github'
    INSIGHTS_ROUTE = 'insights/github'
    ENTITY = '<ADD YOUR ENTITY>'

    def __init__(self):
        self.KEY_TOKEN = os.environ.get('CIRCLE_API_TOKEN')
        if not self.KEY_TOKEN:
            raise ValueError("CIRCLE_API_TOKEN'")
        self.session = requests.Session()
        self.session.headers.update({'Circle-Token': self.KEY_TOKEN})

    def get(self, url):
        return self.session.get(url)

    def get_branches(self, repo="automation"):
        """
        Gets the branches of a particular project
        :param repo:
        :return: Returns a list of branches
        """
        try:
            print('[LOG] Getting Branches')
            url = f'{self.BASE_URL_V2}{self.INSIGHTS_ROUTE}/{self.ENTITY}/{repo}/branches'
            resp = self.get(url)
            resp.raise_for_status()
            data = json.loads(resp.content)
            print('[LOG]', data['branches'])
            return data['branches']
        except Exception as e:
            print(f'[LOG] Error getting branches: \n {e}')


    def get_pipeline_by_branch_name(self, expected_branch_name, os=("android", "ios")):
        """
        Get all the pipeline runs with branch name
        :param expected_branch_name:
        :param os:
        :return: A list of pipeline sorted by created_at
        """
        repo = f"<NAME>-{os}"
        circleCi_pipeline_url = f'https://circleci.com/api/v2/projects/gh/<COMPANY>/{repo}/pipeline'
        pipelines = []

        while len(pipelines) < 100:
            resp = self.get(circleCi_pipeline_url)
            if resp.status_code == 200:
                data = resp.json()
                items = data['items']
                for item in items:
                    if item['project_slug'].endswith('<REPO_NAME_ANDROID>'):
                        if 'vcs' in item and items['vcs']:
                            if 'branch' in item['vcs']:
                                if re.search(expected_branch_name, item['vcs']['branch']):
                                    pipelines.append(item)
                    if item['project_slug'].endswith('<REPO_NAME_IOS>'):
                        if 'trigger_parameters' in item and 'git' in item['trigger_parameters'] and item['trigger_parameters']['git']:
                            git = item['trigger_parameters']['git']
                            if 'branch' in git:
                                if re.search(expected_branch_name, git['branch']):
                                    pipelines.append(item)
                token = data.get('next_page_token')
                if token:
                    circleCi_pipeline_url = f'https://circleci.com/api/v2/projects/gh/<COMPANY>/{repo}/pipeline?{token}'
            else:
                print(f'Error getting pipelines: \n {resp.json}')
                break
        if not pipelines:
            print(f'[LOG] There is not pipeline for the branch name: {expected_branch_name}')
        return pipelines

    def get_latest_pipelines(self, repo, branch=None):
        """
        Get teh list of pipeline runs for the repo. Get up to 250 pipelines
        :param repo:
        :param branch:
        :return: A dict with pipeline id as key and the created at, number and trigger account as a dict value
        """
        print(f'[LOG] Getting latest pipelines for repo: {repo}')
        pipelines = {}
        page_token = None
        url = f'{self.BASE_URL_V2}/{self.PROJECT_ROUTE}/{self.ENTITY}/{repo}/pipeline{f"?branch={branch}" if branch else ""}'
        while len(pipelines) < 250:
            page_url = f'{url}?page-token={page_token}' if page_token else url
            resp = self.get(page_url)
            data = json.loads(resp.content)
            page_token = data['next_page_token']
            for item in data['items']:
                try:
                    pipelines[item['id']] = {
                        'created_at': item['created_at'],
                        'number': item['number'],
                        'user': item['trigger']['actor']['login'],
                    }
                except KeyError as ke:
                    print(f'[LOG] Error getting pipelines: \n {ke}')
            if branch:
                break
        print(f'[LOG] There are {len(pipelines)} pipelines: \n {pipelines}')
        return pipelines

    def get_workflow_from_pipeline(self, pipeline_id):
        """
        Gets the workflows related to the pipeline
        :param pipeline_id:
        :return:
        """
        try:
            print(f'[LOG] Getting workflows for pipeline: {pipeline_id}')
            workflows = []
            url = f'{self.BASE_URL_V2}/pipeline/{pipeline_id}/workflow'
            resp = self.get(url)
            resp.raise_for_status()
            data = json.loads(resp.content)
            for item in data['items']:
                workflows.append({
                    'id': item['id'],
                    'status': item['status'],
                    'name': item['name'],
                })
            print(f'[LOG] There are {len(workflows)} workflows: \n {workflows}')
            return workflows
        except Exception as error:
            print(f'[LOG] Error getting workflows: \n {error}')

    def get_workflow_jobs(self, workflow_id):
        """
        Gets the jobs in the specific Workflow
        :param workflow_id:
        :return: returns a list of the jobs numbers of the jobs related to the workflow
        """
        print(f'[LOG] Getting jobs for workflow: {workflow_id}')
        jobs = []
        job_data = {}
        if not workflow_id:
            return jobs
        url = f'{self.BASE_URL_V2}/workflow/{workflow_id}/job'
        resp = self.get(url)
        body = json.loads(resp.content)
        try:
            for item in body['items']:
                job_data = {
                    'id': item['id'],
                    'status': item['status'],
                    'name': item['name'],
                }
            try:
                job_data['number'] = item['job_number']
            except KeyError:
                job_data['number'] = None
            try:
                job_data['stopped_at'] = item['stopped_at']
            except KeyError:
                job_data['stopped_at'] = None
            try:
                job_data['started_at'] = item['started_at']
            except KeyError:
                job_data['started_at'] = None
            try:
                job_data['approved_by'] = item['approved_by']
            except KeyError:
                job_data['approved_by'] = None
            try:
                job_data['slug'] = item['project_slug']
            except KeyError:
                job_data['slug'] = None
            jobs.append(job_data)
            print(f'[LOG] There are {len(jobs)} jobs: \n {jobs}')
        except KeyError:
            print(f'[LOG] Error getting jobs')
        return jobs

    def get_build_data(self, circle_link):
        build_data = {"workflow_id": circle_link.split('workflow/')[-1]}
        jobs = self.get_workflow_jobs(build_data['workflow_id'])
        for job in jobs:
            if job['name'].endswith('_uat'):
                build_data["uat"] = job['number'] if job['status'] == 'success' else 0
            elif job['name'].endswith('_production'):
                build_data["prod"] = job['number'] if job['status'] == 'success' else 0
            elif job['name'].endswith('_browserstack'):
                build_data["bs"] = job['number'] if job['status'] == 'success' else 0
        return build_data

    def get_latest_develop_build_data(self, platform):
        """
        Get latest build data for develop branch of iOS or Android
        :param platform:
        :return: build data obj
        """
        build_data = None
        # Get the latest successful develop build to cut-off standard cadence
        app_builds_circleci = self.get_latest_pipelines('<REPO_NAME>', "develop")

        for build in app_builds_circleci:
            workflows = self.get_workflow_from_pipeline(build)
            for workflow in workflows:
                if 'test-and-distribute' in workflow['name']:
                    build_data = self.get_build_data(f'workflow/{workflow["id"]}')
                    break
                if build_data and build_data['prod'] and build_data['bs']:
                    return build_data
        return build_data
