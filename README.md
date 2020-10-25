This is a template that contains workflows to automatically update documentation using sphinx, push it to github pages, upload release binaries as assets and do linting using pylama

# How to use this template

## Setup

* First, think of a name for your package. Make shure it's not yet taken on pypi and testpypi
* Second, click 'use this template' in the upper right corner
* Name your repository the name you have just thought of (dashes will be replaced with underscores) and choose a license and description for it. This will enable the setup workflow to automatically fill out the copyright field in setup.py
* Next, in your newly created repository, go to the actions tab, select 'setup' and click on 'run workflow'
* Select your main branch and click 'run workflow'
* You should now see a job 'setup' pop up (after ca. 10 sec, you might have to refresh the page). Wait for it to finish and move on


## Automated distribution on release

* Sign up for an account at testpypi and pypi
* Under account settings (in your pypi account) select API tokens and create a new one with the **permission to upload to the entire account**
* Go to the settings page in your repo and select secrets, click 'add secret' and paste your token from testpypi into a secret named 'TEST_PYPI_PASSWD' and the one from pypi to 'PYPI_PASSWD'
* You are now able to create a release. Choose a tag name that contains only alphanumericals, underscores and dots. If you select 'This is a prerelease', your package will only be uploaded to testpypi, if you don't, it will be uploaded to both
* If this was your first release, go to the settings tab and scroll down to the github pages section. Select gh-pages as the branch to host your docs (it has just been created in the release workflow) and choose root as the directory containing your docs

**Feel free to now edit setup.py, docs/*, readme.md and the folder named like your repo to your liking**
