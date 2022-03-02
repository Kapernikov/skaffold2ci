from pathlib import PosixPath
import pathlib
import yaml
from .gitinfo import should_clone_recursive

class SkaffoldHelmRelease(object):
    def __init__(self, data, project) -> None:
        self.data = data
        self.project = project


class SkaffoldBuildArtifact(object):
    def __init__(self,data, project) -> None:
        self.data = data
        self.project = project
    

    def should_clone_recursive(self):
        project_path = self.project.project_path
        context_path = project_path / self.context()
        return should_clone_recursive(project_path, context_path)

    def image(self):
        return self.data['image']

    def context(self):
        return self.data["context"]
    
    def dockerfile(self):
        if not "docker" in self.data:
            return "Dockerfile"
        if not "dockerfile" in self.data["docker"]:
            return "Dockerfile"
        return self.data["docker"]["dockerfile"]
    
    def requires(self):
        if not "requires" in self.data:
            return []
        #raise Exception(self.data)
        return self.data["requires"]

    def __repr__(self) -> str:
        return f"<{self.image()}:{self.context()}:{self.dockerfile()}>"


class SkaffoldConfiguration(object):
    def __init__(self, data, project_path: PosixPath) -> None:
        self.data = data
        self._validate()
        self.project_path = project_path
    
    def _validate(self):
        apiVersion = self.data["apiVersion"]
        kind = self.data["kind"]
        if kind != "Config":
            raise Exception("Invalid skaffold configuration, expected kind Config but got: {}".format(kind))
        if not apiVersion.startswith("skaffold/v"):
            raise Exception("Invalid skaffold configuration, expected apiVersion starting with skaffold.dev/v but got: {}".format(apiVersion))
    
    def name(self):
        return self.data["metadata"]["name"]

    def artifacts(self):
        return [SkaffoldBuildArtifact(x, self) for x in self.data["build"]["artifacts"]]
    
    def helmReleases(self):
        if not "deploy" in self.data:
            return []
        if not "helm" in self.data["deploy"]:
            return []
        if not "releases" in self.data["deploy"]["helm"]:
            return []
        return self.data["deploy"]["helm"]["releases"]

def parse_skaffold_yaml(fn: str) -> SkaffoldConfiguration:
    """Parse a skaffold.yaml file and return a SkaffoldConfiguration object"""
    with open(fn, "r") as f:
        path = pathlib.PosixPath(fn)
        project_path = path.parent
        return SkaffoldConfiguration(yaml.load(f, Loader=yaml.FullLoader), project_path)
