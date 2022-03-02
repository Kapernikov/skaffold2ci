# Skaffold2CI

Generate a CI pipeline configuration from a skaffold.yaml file. So far, only gitlab is supported.


## Gitlab

Suppose you have a skaffold.yaml in your project root.
The following command will generate a gitlab CI yaml file:

```shell
cd /path/to/project
docker run -it -v $PWD:/opt/source:ro frankdekervel/skaffold2ci \
    skaffold2ci generate-gitlabci --input=/opt/source/skaffold.yaml > .gitlab-ci.yaml
```
