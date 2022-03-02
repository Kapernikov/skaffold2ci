from pathlib import PosixPath
import shutil
import yaml
class HelmChart(object):
    def __init__(self, basedir: PosixPath):
        self.basedir = basedir

    def copyTo(self, targetFolder: PosixPath) -> "HelmChart":
        shutil.copytree(self.basedir,  targetFolder / self.basedir.name)
        return HelmChart(targetFolder / self.basedir.name)

    def zipUp(self):
        shutil.make_archive(str(self.basedir), 'zip', self.basedir)
        shutil.rmtree(self.basedir)

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
