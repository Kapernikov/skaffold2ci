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

The CI will do the following:

* Build all docker images, taking into account the dependencies from the skaffold.yaml. Currently, only one dependency per docker image is supported.
* Only run automatically when the current commit is tagged with a semver tag (eg "v0.4.2"). Otherwise, it can run but must be started by hand.
* After building all docker images, a helm chart will be published to gitlabs built-in package registry. The helm chart will already have the `artifactOverrides` from skaffold.yaml taken into account. This way, version 0.4.2 of your helm chart will refer to version 0.4.2 of all docker images.

Optional: automatic creation of a gitlab release with changelog based on `git-chglog`.
To do this, first generate a `git-chglog` configuration:

```shell
cd /path/to/project
mkdir .chglog
docker run -it -v $PWD:/opt/source:ro frankdekervel/skaffold2ci \
    skaffold2ci generate-chglog-config --repository-url=https://gitlab.com/our/cool/repo > .chglog/config.yml
```

Now, if you re-generate the gitlab CI (see above command), it will detect the configuraiton and emit extra steps, to create a changelog and to create a release automatically whenever you tag a commit with a semver tag.
Unfortunately, a gitlab release can not be made using the gitlab CI token, neither can it be made using a deploy token. So you will have to create a personal token for this and configure it as a variable under settings->ci_cd.
You will have to name this variable `CREATE_RELEASE_TOKEN`, and you can **not** mark it as protected, but you need to mark it as masked.
