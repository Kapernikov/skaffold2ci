from pathlib import PosixPath
import shutil
import yaml
import os
from .gitinfo import Semver
class HelmChart(object):
    def __init__(self, basedir: PosixPath):
        self.basedir = basedir

    def copyTo(self, targetFolder: PosixPath) -> "HelmChart":
        shutil.copytree(self.basedir,  targetFolder / self.basedir.name)
        return HelmChart(targetFolder / self.basedir.name)

    def zipUp(self, semver: Semver):
        shutil.make_archive(str(self.basedir) + "-" + str(semver), 'gztar', self.basedir)
        shutil.rmtree(self.basedir)
        os.rename(str(self.basedir) + "-" + str(semver) + ".tar.gz", str(self.basedir) + "-" + str(semver) + ".tgz")

    def fixVersion(self, semver: Semver):
        with open(str(self.basedir / "Chart.yaml")) as f:
            y = yaml.load(f, Loader=yaml.FullLoader)
        y["version"] = semver.getVersion()
        with open(self.basedir / "Chart.yaml", "w") as f:
            yaml.dump(y, f)

    def fixArtifactOverrides(self, artifactOverrides: list, prefix: str, suffix: str):
        with open(str(self.basedir / "values.yaml")) as f:
            y = yaml.load(f, Loader=yaml.FullLoader)
        for k,v in artifactOverrides.items():
            path = k.split(".")
            root = y
            for p in path[:-1]:
                #if not p in root:
                #    root[p] = {}
                root = root[p]
            root[path[-1]] = prefix + v + suffix
        with open(self.basedir / "values.yaml", "w") as f:
            yaml.dump(y, f)
