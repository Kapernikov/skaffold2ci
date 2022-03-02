from pathlib import PosixPath
import os
def is_submodule(main_project_path: PosixPath, submodule_path: PosixPath) -> bool:
    """Check if a submodule is a submodule of the main project"""
    while submodule_path != main_project_path:
        git_folder = submodule_path / ".git"
        if git_folder.exists():
            return True
        submodule_path = submodule_path.parent
    return False


def contains_git_folder(path: PosixPath) -> bool:
    """Check if a path contains a .git folder"""
    for p in path.rglob(".git"):
        return True
    return False

def should_clone_recursive(main_project_path: PosixPath, context: PosixPath) -> bool:
    """Check if a submodule should be cloned recursively"""
    if is_submodule(main_project_path, context):
        return True
    if contains_git_folder(context):
        return True
    return False


class Semver(object):
    def __init__(self, version: str):
        if "-" in version:
            self.extraversion = "-".join(version.split("-")[1:])
        else:
            self.extraversion = ""
        if version.startswith("v"):
            version = version[1:]
        self.version = version.split("-")[0]
        self.major = int(self.version.split(".")[0])
        self.minor = int(self.version.split(".")[1])
        self.patch = int(self.version.split(".")[2])

    def getVersion(self) -> str:
        ev = self.extraversion
        if ev != "":
            ev = "-" + ev
        return f"{self.major}.{self.minor}.{self.patch}{ev}"

    def __repr__(self) -> str:
        ev = self.extraversion
        if ev != "":
            ev = "-" + ev
        return f"v{self.major}.{self.minor}.{self.patch}{ev}"

def getSemver(inputfolder: PosixPath):
    if inputfolder.is_file():
        inputfolder = inputfolder.parent
    latest_tag = os.popen(f"cd {inputfolder}; git describe --tags --abbrev=0 2>/dev/null").read().strip()
    if latest_tag == "":
        return Semver("0.0.0-noversion")
    else:
        return Semver(latest_tag)
