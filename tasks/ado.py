import json
from invoke import task

@task(help={"organization": "Azure DevOps organization.",
            "project": "Azure DevOps project."})
def config(c, organization=None, project=None):
    """Configure az devops cli, uses values from invoke.yaml by default."""
    if organization is None:
        organization = c.ado.organization
    if project is None:
        project = c.ado.project
    cmd = f"az devops configure --defaults organization=\"{organization}\" project=\"{project}\""
    print(cmd)
    c.run(cmd)

@task(help={"name": "Name of repository.",
            "open": "Open the repository page in your web browser."})
def repo_create(c, name=None, open=False):
    """Create az devops repository, uses values from invoke.yaml by default."""
    if name is None:
        name = c.ado.repository.name
    cmd = f"az repos create --name=\"{name}\""
    if open:
        cmd += " --open"
    c.run(cmd, echo=True)


# TODO: Automate git setup

# @task(help={"name": "Name of repository."})
# def add_origin(c, name=None):
#     """Show az devops repository, uses values from invoke.yaml by default."""
#     if name is None:
#         name = c.ado.repository.name
#     # Get info from repo
#     cmd = f"az repos show --repository=\"{name}\" --query sshUrl"
#     url = c.run(cmd, echo=True)
#     print(url)

#     c.run("git init", echo=True)
#     c.run(f"git remote add origin {url}", echo=True)

@task(
    help={
        "organization": "Azure DevOps organization.",
        "project": "Azure DevOps project.",
        "pipelineId": "Id of the Azure DevOps pipeline. It can be found in the Azure Devops url under definitionID.",
        "pat": "Personal Access Token used to query the Azure DevOps API. The required permission is 'Build - read & execute'"
})
def resolve_pipeline(c, organization=None, project=None, pipelineId=None, pat=None):
    """Resolve the pipeline of the project. This will import and resolve all templates.
    The final yaml file is saved in azure-pipelines-resolved.yml

    curl, Jq and yq(python) are required

    Reference: https://docs.microsoft.com/en-us/rest/api/azure/devops/pipelines/runs/run-pipeline?view=azure-devops-rest-6.1
    """
    
    with open('azure-pipelines.yml') as f:
        content = f.read()
    pipeline_content = json.dumps(content).replace("'", r"'\''")
    request_body = f'{{"previewRun": true, "yamlOverride": {pipeline_content} }}'
    cmd = f"""curl -s -u :{pat}  -H 'Content-Type: application/json' -d '{request_body}' https://dev.azure.com/{organization}/{project}/_apis/pipelines/{pipelineId}/runs\?api-version\=6.1-preview.1 > .api_response"""
    c.run(cmd, echo=True)
    cmd = f"""cat .api_response | jq .finalYaml | yq -r > azure-pipelines-resolved.yml"""
    c.run(cmd, echo=True)
    
