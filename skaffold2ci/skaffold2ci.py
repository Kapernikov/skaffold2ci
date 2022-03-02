import click
from pathlib import PosixPath, Path
from .gitlabci import GitlabCi
from .skaffoldyaml import parse_skaffold_yaml
import inspect
import os
from skaffold2ci import gitinfo, gitlabci
from .helmfixer import HelmChart
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

def get_my_int(number: int) -> int:
    """Function returning the same number it receives"""
    return number



@click.group()
@click.pass_context
def main(ctx):
    pass


@main.command()
@click.pass_context
@click.option("--input", default="skaffold.yaml", type=click.Path(exists=True), help="The skaffold.yaml file to read")
@click.option('--publish-helm/--no-publish-helm', default=True)
def generate_gitlabci(ctx, input: str, publish_helm: bool):
    """Generate a GitLab CI configuration from a skaffold.yaml file"""
    skaffold = parse_skaffold_yaml(input)
    ci = gitlabci.buildFromSkaffold(skaffold)
    if (publish_helm):
        ci.addJob(gitlabci.PublishChartJob([x.chartFolderName() for x in skaffold.helmReleases()]))
    folder = Path(input).parent / ".chglog"
    if (folder.exists()):
        ci.addJob(gitlabci.CreateReleasenotesJob())
        ci.addJob(gitlabci.CreateGitlabReleaseJob())
    print(ci.toYaml())


@main.command(help="Create zipped charts with the skaffold artifactOverrides applied")
@click.pass_context
@click.option("--input", default="skaffold.yaml", type=click.Path(exists=True), help="The skaffold.yaml file to read")
@click.option("--outputdirectory", required=True, type=click.Path(dir_okay=True, file_okay=False), help="The output directory to write the frozen helm charts")
@click.option("--prefix", required=True, type=str, help="the prefix for the images")
@click.option("--suffix", required=True, type=str, help="the suffix for the images")
def freezecharts(ctx, input: str, outputdirectory: str, prefix: str, suffix: str):
    skaffold = parse_skaffold_yaml(input)
    semver = gitinfo.getSemver(Path(input))
    for release in skaffold.helmReleases():
        if release.chartPath():
            chart = HelmChart(skaffold.project_path /  release.chartPath())
            chart = chart.copyTo(Path(outputdirectory))
            chart.fixArtifactOverrides(release.artifactOverrides(), prefix, suffix)
            chart.fixVersion(semver)
            chart.zipUp(semver)


@main.command(help="Upload frozen charts to gitlab")
@click.pass_context
@click.option("--input", default="skaffold.yaml", type=click.Path(exists=True), help="The skaffold.yaml file to read")
@click.option("--outputdirectory", required=True, type=click.Path(dir_okay=True, file_okay=False), help="The output directory that contains the frozen charts")
@click.option("--gitlab-token", default=os.getenv("CI_JOB_TOKEN",""), type=str, help="gitlab token")
@click.option("--gitlab-url", default=os.getenv("CI_API_V4_URL",""), type=str, help="gitlab V4 api url")
@click.option("--gitlab-username", default="gitlab-ci-token", type=str, help="username of deploy token")
@click.option("--gitlab-project-id", default=os.getenv("CI_PROJECT_ID",""), type=str, help="gitlab project ID")
def gitlab_upload_frozen_charts(ctx, input: str, outputdirectory: str, gitlab_token: str, gitlab_url: str, gitlab_project_id: str, gitlab_username: str):
    skaffold = parse_skaffold_yaml(input)
    semver = gitinfo.getSemver(Path(input))
    for release in skaffold.helmReleases():
        if release.chartPath():
            zipf = os.path.join(outputdirectory,release.chartFolderName() + "-" + str(semver) + ".tgz")
            with open(zipf, "rb") as f:
                files = {"chart": f}
                data = {"token": gitlab_token}
                channel = "stable"
                auth = HTTPDigestAuth(gitlab_username, gitlab_token)
                r = requests.post(f"{gitlab_url}/projects/{gitlab_project_id}/packages/helm/api/{channel}/charts", files=files, data=data, auth=auth)
                if (r.status_code < 200 or r.status_code >= 300):
                    print(r.text)
                    print(r.status_code)
                    print("Failed to upload chart, retry with basic auth")
                auth = HTTPBasicAuth(gitlab_username, gitlab_token)
                r = requests.post(f"{gitlab_url}/projects/{gitlab_project_id}/packages/helm/api/{channel}/charts", files=files, data=data, auth=auth)
                if (r.status_code < 200 or r.status_code >= 300):
                    print(r.text)
                    print(r.status_code)
                    raise Exception("Failed to upload chart, both digest and basic auth failed")


@main.command(help="Generate contents of .chglog/config.yml")
@click.pass_context
@click.option("--repository-url", required=True, type=str, help="URL of git repo")
def generate_chglog_config(ctx, repository_url):
    print(gitlabci.template_cghlog_config_yaml(repository_url))
    

@main.command(help="Generate contents of .chglog/CHANGELOG.tpl.md")
@click.pass_context
def generate_changelog_template(ctx):
    print(gitlabci.template_chglog_template())

if __name__ == "__main__":
    main()
