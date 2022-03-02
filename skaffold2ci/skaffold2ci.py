import click
from pathlib import PosixPath, Path
from .gitlabci import GitlabCi
from .skaffoldyaml import parse_skaffold_yaml
from skaffold2ci import gitlabci
from .helmfixer import HelmChart

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
def generate_gitlabci(ctx, input: str):
    """Generate a GitLab CI configuration from a skaffold.yaml file"""
    skaffold = parse_skaffold_yaml(input)
    ci = gitlabci.buildFromSkaffold(skaffold)
    print(ci.toYaml())


@main.command()
@click.pass_context
@click.option("--input", default="skaffold.yaml", type=click.Path(exists=True), help="The skaffold.yaml file to read")
@click.option("--outputdirectory", required=True, type=click.Path(dir_okay=True, file_okay=False), help="The output directory to write the frozen helm charts")
@click.option("--prefix", required=True, type=str, help="the prefix for the images")
@click.option("--suffix", required=True, type=str, help="the suffix for the images")
def freezecharts(ctx, input: str, outputdirectory: str, prefix: str, suffix: str):
    skaffold = parse_skaffold_yaml(input)
    for release in skaffold.helmReleases():
        if "chartPath" in release:
            chart = HelmChart(skaffold.project_path /  release["chartPath"])
            chart = chart.copyTo(Path(outputdirectory))
            chart.fixArtifactOverrides(release["artifactOverrides"], prefix, suffix)
            chart.zipUp()


if __name__ == "__main__":
    main()
