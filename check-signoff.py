#!/usr/bin/env python3
import os
import requests
import re
REPO = os.environ.get("BUILDKITE_PULL_REQUEST_REPO")
PR_NUMBER = int(os.environ.get("BUILDKITE_PULL_REQUEST"))
SIGN_OFF_LINK = os.environ.get("SIGNOFF_URL", "No url provided")
signOffRegex = re.compile('Signed-off-by: (\w+\s\w+) <\S+>', re.IGNORECASE)

def fetchBodyAndCommits():
    GITHUB_URL="https://api.github.com/graphql"
    query = """
    query($repoName: String!, $login: String!, $prNumber: Int!) {
        organization(login: $login) {
            repository(name: $repoName){
                pullRequest(number: $prNumber) {
                    bodyText
                        commits(first: 20) {
                            nodes {
                                commit {
                                messageBody
                            }
                        }
                    }
                }
            }
        }
    }
    """
    owner, repo = REPO[len("git://github.com/"):].split("/")
    variables = {
        "repoName": repo.replace(".git", ""),
        "login": owner,
        "prNumber": PR_NUMBER,
    }
    r = requests.post(GITHUB_URL,
        json={
            "query": query,
            "variables": variables
        }, headers={
            "Authorization": "Bearer %s" % os.environ.get("GITHUB_TOKEN")
    })
    pr = r.json()['data']['organization']['repository']['pullRequest']
    if pr is None:
        print("🔥  PR was not found. Your CI is probably misconfigured")
        exit(1)

    return (
        pr['bodyText'],
        [commit['commit'].get('messageBody', None) for commit in pr['commits']['nodes']]
    )

def isSignedOff(body, commits):
    if signOffRegex.search(body):
        print("Sign off found in body")
        return True
    for commit in commits:
        if signOffRegex.search(commit):
            print("Sign off found in a commit")
            return True
    return False


text, commits = fetchBodyAndCommits()
if isSignedOff(text, commits):
    exit(0)
else:
    print("🕴️  You must sign off on this PR. See %s" % SIGN_OFF_LINK)
    exit(1)