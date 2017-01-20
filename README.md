# CMS related tools

This directory contains all the CMS related tools

This document will guide you through the automation of new CMS projects (from
the RM side). This repository contains a set of scripts to make full use of
gitlab pipelines.

This project provides a set of tools to automate the boring part of the
automation: creating configuration files, accounts and password for each step.

The main area of automation are:
* <a href="#gitlab_automation">gitlab automation</a>
* <a href="#ansible_automation">ansible automation</a>
* <a href="#ansible_tower_automation">ansible tower automation</a>
* <a href="#artifactory_automation">artifactory automation</a>


# prerequisites
This set of tools relies on few external python libraries, to install of the
requirements exectue the `start_me.sh` script available in this directory.
This script will take care of installing all the python dependencies and switch
to the right python virtualenvironment: `rm-automation`

```
./start_me.sh
* create python virutal environment
* install python dependencies (logs: $HOME/git/braindump/cms/start_me.log)

now execute: source $HOME/.virtualenvs/rm-automation/bin/activate
```

> __Important__: do not forget to execute "source $HOME/.virtualenvs/rm-automation/bin/activate"


# gitlab automation <a name="gitlab_automation"></a>
__state__: complete, tracked by [NWR-3347](http://jira2.esl-asia.com:8080/browse/NWR-3347)


This section will guide you to gitlab automation. First step, get a token from gitlab.
This token will be used to access the gitlab API. Please note all the changes made
by this tool will be linked to the owner of the giltab API token, so don't share
this token with anybody.


## get a private token from gitlab
In order to use the gitlab automation, we need a private gitlab token, you can
get your own from the [personal access token url](https://gitlab.ph.esl-asia.com/profile/personal_access_tokens)


## gitlab configuration <a name"gitlab_configuration"></a>
create a file named ``~/.python-gitlab.cfg`` with the following content:

```
[global]
timeout = 10
default = gitlab.ph.esl-asia.com
ssl_verify = false

[gitlab.ph.esl-asia.com]
url = https://gitlab.ph.esl-asia.com
private_token = <your private token>

[http://trc-ptc-afact01.msred.dom:8081/artifactory]
username = <your username>
password = <your password>

[http://mic-pele-artifact.msred.dom:8081/artifactory]
username = <your username>
password = <your password>

[https://mic-tst-itass01.msgreen.dom]
username = <your username>
password = <your password>

[https://msc-co-itass01.msorange.dom]
username = <your username>
password = <your password>

[https://trc-ptc-itass01.msred.dom]
username = <your username>
password = <your password>
```


Replace ``<your private token>`` with the one obtained in [get a private token from gitlab]

> __note__: as a reference, there's a copy of the configuration file in `examples/python-gitlab.cfg`

now we are ready to execute the gitlab automation.

## automating gitlab projects
gitlab automation is managed by the ``gitlab-automation.py`` script. In this
section we assume your gitlab configuration is already set, you're on the right
python virtual environment with all the dependencies installed.
When this is done, the gitlab automation is easy as running:

```
python ./gitlab-automation.py --project-url <url> --jira-issue <jira issue>
```
where:
* __url__ is the https or ssh url of the project you're going to automate
* __jira issue__ is the ticket number that tracks this project automation

### what does this script do?
This script creates the basic automation as follows:
* clones the project locally, in a temporary directory
* creates a new branch named after the __jira issue__
* creates the .gitlab-ci.yml from a template
* copies the ``templates/build`` directory into the local working copy
* creates the deploy.json file from a template
* commits all the changes
* pushes the changes to the remote repository
* creates a pull request

The automation becomes active after the pull request is approved and a runner is
connected to the project (TODO). What is left to do is fine tuning the list of
approvers in deploy.json file
> TODO: create and activate a builder for each project

Even if automation becomes active, it will still fail: we still need to
configure Artifactory (so we can upload and download artifacts) and then we
also need to configure Ansible (and Ansible tower), at the moment we only have
pipelines in place. Let's start from Artifactory

# artifactory automation <a name="artifactory_automation"></a>
__state__: complete, tracked by [NWR-3350](http://jira2.esl-asia.com:8080/browse/NWR-3350)


Artifactory the service that allow us to store built artifacts. Artifactory is
fundamental as it helps us to completely decouple build and deployments.
After an artifact is uploaded we can deploy it in all the environments as many
times we want.

conventions:
>__important__: In artifactory world, a deployment is an upload of a binary
(comes from maven)
.
### artifactory instances
we have one artifactory instance for every data center

### repository
Any given project will be deployed (uploaded) in a repository named after the
product itself. Expect project `new-cms` to upload artifacts in a `new-cms`
repository.

### archive names
every project generates ``<project>-<version>.tar.gz`` archives. At the moment
it's not an option to decide the package name by the developers as the package
is create only for the deployment stage and it's consumed only by the
deployment stage (developers cannot download anything from artifactory - by
design) but they can still access the package generated by the build as Gitlab
artifact. Gitlab artifactory are avalilabe to any project memebers and they are
only there for reference. RM team ignores them.  Please note the Gitlab package
only live few days (7 at the moment) because we cannot wast space to store an
infinte numner of builds.


### user and permissions
the script will create a new user, called after the project with "Deploy/Cache"
and "Read" permissions.
This user will be able to read (used by ansible to download artifacts) and
upload (used by gitlab to upload the artifact). This set of permissions do
no allow to overwrite artifacts. Artifacts can only be deleted by admins.


## How to trigger the artifactory automation
Artifactoy automation is managed by the ``artifactory-automation.py`` script. In this
section we assume your configuration is already set, you're on the right
python virtual environment with all the dependencies installed.
When this is done, the gitlab automation is easy as running:

```
python ./artifactory-automation.py --project-url <url>
```

where:
* __url__ is the https or ssh url of the project you're going to automate


## How does the artifactory automation works?
The artifactory automation needs the following information to be executed:
* project url: where's your project stored in git?
* jira issue: if you're running this there must be a ticket

At the super high overview, this script executes:
* creates a repository in artifactory named after the project
* creates a new artifactory user named after the project
* sets the permission for the new user to the new repostory so it can only "deploy"
  (upload) and not overwrite anything.


# How do passwords are created/maintained?
This script gets the passwords from the artifactory project. If you update the
gitlab passwords in this project, run this script again, it will take care of
refreshing the passwords on the artifactory side.
<a href="#gitlab_configuration">gitlab API</a>


# ansible automation <a name="ansible_tower_automation"></a>
__state__: not done yet. Tracked by [NWR-3348](http://jira2.esl-asia.com:8080/browse/NWR-3348)

# ansible tower automation <a name="ansible_tower_automation"></a>
__state__: not done yet. Tracked by [NWR-3349](http://jira2.esl-asia.com:8080/browse/NWR-3349)

