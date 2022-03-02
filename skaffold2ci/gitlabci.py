import yaml
import inspect
from .skaffoldyaml import SkaffoldConfiguration
from typing import List


class PublishChartJob(object):
    def __init__(self, helm_chart_names: List[str]):
        self.helm_chart_names = helm_chart_names

    def toYaml(self):
        piece1 =  inspect.cleandoc("""
            publish-helm-chart:
                stage: publish_package
                image: frankdekervel/skaffold2ci:latest
                script:
                    - export TG=${CI_COMMIT_TAG}; [[ -z ${TG} ]] && export TG=${CI_COMMIT_SHORT_SHA}
                    - mkdir -p /opt/target
                    - cd ${CI_PROJECT_DIR} && skaffold2ci freezecharts --input=skaffold.yaml --outputdirectory=/opt/target --prefix=${CI_REGISTRY_IMAGE}/ --suffix=:${TG}
                    - cd ${CI_PROJECT_DIR} && skaffold2ci gitlab-upload-frozen-charts --input=skaffold.yaml --outputdirectory=/opt/target
                artifacts:
                    paths:
        """)
        h = "\n" + "\n".join([f"            - /opt/target/{x}.zip" for x in self.helm_chart_names]) + "\n"
        piece2 = inspect.cleandoc("""
            # rules
                rules:
                    - if: $CI_COMMIT_TAG =~ /^v\d+.\d+.\d+/
                      when: always
                    - when: manual
        """)
        return piece1 + h + piece2

def _get_kaniko_template():
    return inspect.cleandoc("""
        .build-container-kaniko: &build-container
            image:
                name: gcr.io/kaniko-project/executor:debug
                entrypoint: [""]
            rules:
                - if: '$CI_COMMIT_BRANCH == "master"'
                  changes:
                    - "${FOLDER}"
                  when: manual
                - if: $CI_COMMIT_TAG =~ /^v\d+.\d+.\d+/
                  when: always
                - when: manual
            variables:
                TARGET: UNKNOWN
                DOCKERFILE: UNKNOWN
                FOLDER: UNKNOWN
                DOCKER_ARGS: ""
                FROMIMG: ""
                FROMIMG_ALIAS: ""
            script:
                - mkdir -p /kaniko/.docker && export KANIKO_EXTRA=""
                - echo "{\\"auths\\":{\\"${CI_REGISTRY}\\":{\\"auth\\":\\"$(printf "%s:%s" "${CI_REGISTRY_USER}" "${CI_REGISTRY_PASSWORD}" | base64 | tr -d '\\n')\\"}}}" > /kaniko/.docker/config.json
                - export TG=${CI_COMMIT_TAG}; [[ -z ${TG} ]] && export TG=${CI_COMMIT_SHORT_SHA}
                - echo "dockerfile would be ${CI_PROJECT_DIR}/${FOLDER}/${DOCKERFILE}, target would be ${CI_REGISTRY_IMAGE}/${TARGET} and context would be ${CI_PROJECT_DIR}/${FOLDER}"
                - echo; [[ "${FROMIMG}" != "" ]] && export KANIKO_EXTRA="--build-arg ${FROMIMG_ALIAS}=${CI_REGISTRY_IMAGE}/${FROMIMG}:${TG}"
                - >-
                  /kaniko/executor
                  --cache=true
                  --cache-copy-layers=true
                  --cache-ttl=300h
                  --use-new-run
                  --snapshotMode=redo
                  --context "${CI_PROJECT_DIR}/${FOLDER}"
                  --dockerfile "${CI_PROJECT_DIR}/${FOLDER}/${DOCKERFILE}"
                  --destination "${CI_REGISTRY_IMAGE}/${TARGET}:${TG}"
                  --destination "${CI_REGISTRY_IMAGE}/${TARGET}:latest"
                  ${KANIKO_EXTRA}
                """)


class CreateReleasenotesJob(object):
    def toYaml(self) -> str:
        return inspect.cleandoc("""
                releasenotes:
                    stage: publish_package
                    image: 
                        name: quay.io/git-chglog/git-chglog
                        entrypoint: [""]
                    rules:
                        - if: $CI_COMMIT_TAG =~ /^v\d+.\d+.\d+/
                          when: always
                        - when: manual
                    script:
                        - export CUR_RELEASE=$(git describe --tags --abbrev=0)
                        - export PREV_RELEASE=$(git describe --tags --abbrev=0 ${CUR_RELEASE}^)
                        - git-chglog $CUR_RELEASE > relnotes.txt
                    artifacts:
                        expire_in: '1 hour'
                        paths:
                            - relnotes.txt
        """)

class CreateGitlabReleaseJob(object):
    def toYaml(self) -> str:
        return inspect.cleandoc("""
                create-gitlab-release:
                    stage: create_release
                    image: python:3.7-buster
                    needs: ["releasenotes"]
                    rules:
                        - if: $CI_COMMIT_TAG =~ /^v\d+.\d+.\d+/
                          when: always
                        - when: manual
                    script:
                        - pip3 install gitlab-release
                        - gitlab-release --private-token "${CREATE_RELEASE_TOKEN}" --description "`cat relnotes.txt`" relnotes.txt
        """)


class BuildContainerJob(object):
    def __init__(self, name, context, dockerfile, requires) -> None:
        self.name = name
        self.context = context
        self.dockerfile = dockerfile
        self.requires = requires
        self.extravars = {}
        if len(self.requires) > 1:
            raise Exception("multiple requires not yet supported")

    
    def toYaml(self) -> str:
        d = {
            "stage": "build_containers",
            "variables": {
                "TARGET": self.name,
                "DOCKERFILE": self.dockerfile,
                "FOLDER": self.context,
            }
        }
        if len(self.requires) > 0:
            d["variables"]["FROMIMG"] = self.requires[0]["image"]
            d["variables"]["FROMIMG_ALIAS"] = self.requires[0]["alias"]
            d["needs"] = ["build-" + self.requires[0]["image"]]
        
        for k,v in self.extravars.items():
            d["variables"][k] = v

        data = {"build-" + self.name: d}
        lines = yaml.dump(data).split("\n")
        lines.insert(1, "  <<: *build-container")
        return "\n".join(lines)
        




class GitlabCi(object):
    def __init__(self) -> None:
        self.stages = ["build_containers", "publish_package", "create_release"]
        self.jobs = []


    def addJob(self, j):
        self.jobs.append(j)

    def toYaml(self):
        data = {"stages": self.stages}
        
        piece1 =  yaml.dump(data)
        piece2 = _get_kaniko_template()

        jobs = "\n\n".join([j.toYaml() for  j in self.jobs])

        return piece1 + "\n\n" + piece2 + "\n\n" + jobs

def addBuildJobsFromSkaffold(s: SkaffoldConfiguration, ci: GitlabCi):
    for a in s.artifacts():
        job = BuildContainerJob(a.image(), a.context(), a.dockerfile(), a.requires())
        if a.should_clone_recursive():
            job.extravars["GIT_SUBMODULE_STRATEGY"] = "recursive"
        ci.jobs.append(job)
    

def buildFromSkaffold(s: SkaffoldConfiguration) -> GitlabCi:
    ci = GitlabCi()
    addBuildJobsFromSkaffold(s, ci)
    return ci


def template_cghlog_config_yaml(repository_url: str):
    return inspect.cleandoc(f"""
        style: gitlab
        template: CHANGELOG.tpl.md
        info:
          title: CHANGELOG
          repository_url: {repository_url}
        options:
          commits:
             filters:
               Type:
                 - feat
                 - fix
                 - perf
                 - refactor
                 - docs
          commit_groups:
            title_maps:
              feat: Features
              fix: Bug Fixes
              perf: Performance Improvements
              refactor: Code Refactoring
              docs: Documentation changes
          header:
            pattern: "^(\\\\w*)(?:\\\\(([\\\\w\\\\$\\\\.\\\\-\\\\*\\\\s]*)\\\\))?\\\\:\\\\s(.*)$"
            pattern_maps:
              - Type
              - Scope
              - Subject
          notes:
            keywords:
              - BREAKING CHANGE
    """)

def template_chglog_template():
    return inspect.cleandoc("""
        {{-  range .Versions }}
        ## {{ if .Tag.Previous }}[{{ .Tag.Name }}]{{ else }}{{ .Tag.Name }}{{ end }} - {{ datetime "2006-01-02" .Tag.Date }}

        {{ range .CommitGroups -}}
        ### {{ .Title }}
        {{ range .Commits -}}
        - {{ if .Scope }}**{{ .Scope }}:** {{ end }}{{ .Subject }}
        {{ end }}
        {{ end -}}

        {{- if .RevertCommits -}}
        ### Reverts
        {{ range .RevertCommits -}}
        - {{ .Revert.Header }}
        {{ end }}
        {{ end -}}

        {{- if .MergeCommits -}}
        ### Merge Requests
        {{ range .MergeCommits -}}
        - {{ .Header }}
        {{ end }}
        {{ end -}}

        {{- if .NoteGroups -}}
        {{ range .NoteGroups -}}
        ### {{ .Title }}
        {{ range .Notes }}
        {{ .Body }}
        {{ end }}
        {{ end -}}
        {{ end -}}
        {{ end -}}
    """)
