![Github-Gitlab-Atuo-Deploy](http://olipo186.github.com/Github-Gitlab-Auto-Deploy/images/Github-Gitlab-Auto-Deploy.png)

# What is it?

this is a small HTTP server written in python. 
It allows you to have a version of your project installed, that will be updated automatically on each Github or Gitlab push.

To set it up, do the following:
*   install python
*   copy the GitAutoDeploy.conf.json.example to GitAutoDeploy.conf.json. This file will be gitignored and can be environment specific.
*   enter the matching for your project(s) in the GitAutoDeploy.conf.json file
*   start the server by typing "python GitAutoDeploy.py" 
*   to run it as a daemon add **daemon-mode**
*   On the Github or Gitlab page go to a repository, then "Admin", "Service Hooks", 

"Post-Receive URLs" and add the url of your machine + port (e.g. http://example.com:8001).

You can even test the whole thing here, by clicking on the "Test Hook" button, whohoo!

# How this works

When someone pushes changes into Github or Gitlab, it sends a json file to the service hook url. 
It contains information about the repository that was updated.

All it really does is match the repository urls to your local repository paths in the config file, 
move there and run `git pull`.

Additionally it runs a deploy bash command that you can add to the config file optionally.
Make sure that you start the server as the user that is allowed to pull from the github or gitlab repository.

## Email sending

It's possible to specify a gmail account, and several recipient addresses.
On a git post-receive event the script will send

*   each commits included in the `git push`
*   the system output for the `git pull` from the server
*   the output of the optional `deploy` command - from the server

## Specify the "deploy" branch

By default the script would run the

*   `git pull`
*   deploy command
*   email sending

On each and every `git push` command.

It's also possible to specify a `ref` option for each repository and that
would only trigger the commands above if the pushed branch is the same

## Sample config

    {
        "port": 8001,

        "gmail": {
            "username": "yourgmailuser@gmail.com",
            "password": "yourgmailpassword",
            "recipients": ["anyrecipient@gmail.com"]
        },

        "repositories":
        [{
            "url": "https://github.com/logsol/Test-Repo",
            "path": "/home/logsol/projects/Test-Repo",
            "ref": "refs/heads/master",
            "deploy": "echo deploying"
        },
        {
            "url": "https://github.com/logsol/Katharsis-Framework",
            "path": "/home/logsol/projects/Katharsis-Framework",
            "ref": "refs/heads/staging"
        }]
    }


