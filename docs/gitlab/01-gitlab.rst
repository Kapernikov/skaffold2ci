Gitlab
~~~~~~
.. warning::
    This part is still under construction. Documentation needs to be updated. Gitlab as devops framework needs to be documented and tested. 
    At the moment this is an assembly of former docs.



In order to successfully publish to an artifacts storage, you will need to define a few environment variables in Gitlab:

- `$SERVER_URL`: URL of the PyPi server or of the Azure Artifacts Feed
- `$SERVER_USERNAME`
- `$SERVER_PASSWORD`

These project level environment variables can be set using::

    curl --request POST --header "PRIVATE-TOKEN: <your_access_token>" "https://gitlab.com/api/v4/projects/NAMESPACE/PROJECT_NAME/variables" --form "key=NEW_VARIABLE" --form "value=new value"

You can find more info in the Gitlab documentation `to set it up via the API <https://gitlab.com/help/api/project_level_variables.md>`_ or `to set it up manually <https://docs.gitlab.com/ee/ci/variables>`_.

Enable code coverage by enabling test coverage parsing by going to the Gitlab project > settings > CI/CD > General Pipelines.
