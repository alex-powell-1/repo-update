# repo-update

Validates incoming webhook from github and restarts service associated with webhook. 

## Includes:
repo-update.service - Service configured to work with amazon EC2 default settings.
restart.sh is a script to be used as 

## Usage

** Note: You must have ssh keys setup for your EC2 Instance so you don't have to put in a password. 


In the repos variable, you put in as many repos as you like. 
repos = [
    {
        "name": "",  # Name of the repository
        "path": "",  # Path to the repository
        "webhook_secret": "",  # Secret key for the webhook
        "service_name": "",  # Name of the service to restart
        "will_pip_install": True,  # If True, will run pip install -r requirements.txt
    },
    # Add more repositories here
]