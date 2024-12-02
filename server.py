import flask
from flask import request, jsonify
import hmac
import hashlib
from datetime import datetime
import subprocess

from threading import Thread


app = flask.Flask(__name__)

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

LOGFILE = "logs/webhook_updates.log"


def log(message: str):
    with open(LOGFILE, "a") as log:
        msg = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}"
        print(msg, file=log)
        print(msg)

    try:
        pass

    #     def task():
    #         requests.post(
    #             "http://localhost:3600/log",
    #             json={
    #                 "program": "Repo Update",
    #                 "message": message,
    #                 "level": "INFO",
    #             },
    #         )

    #     t = Thread(target=task)
    #     t.start()
    except Exception:
        pass


def is_master_branch(ref: str):
    return ref in ["refs/heads/main", "refs/heads/master"]


log("Webhook Update Server Starting")


def run_command(command: str, directory: str):
    log(f"Running command: {command} in {directory}")
    subprocess.run(
        f"cd {directory} && {command}",
        capture_output=False,
        shell=True,
        stdout=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )


@app.errorhandler(Exception)
def handle_exception(e):
    # Return a JSON response with a generic error message
    log(f"Error - {e}")
    return jsonify({"error": "Internal Server Error"}), 500


threads: dict[str, Thread] = {}


@app.route("/repo_update", methods=["POST"])
def repo_update():
    """Receives a POST request from GitHub Webhook, validates the webhook, and then restarts the services"""

    log("Message Received")

    signature = request.headers.get("X-Hub-Signature-256")
    if signature is None:
        log("No Signature. Returning 400")
        return "", 400

    sha_name, signature = signature.split("=")
    if sha_name != "sha256":
        log("Invalid Signature Format. Returning 400")
        return "Invalid signature format", 400

    # Get webhook secret and repository path from the repository name
    webhook_secret = None
    repo_path = None
    repo_name = request.json["repository"]["name"]
    service_name = None
    will_pip_install = False
    for repo in repos:
        if repo["name"] == repo_name:
            webhook_secret = repo["webhook_secret"]
            repo_path = repo["path"]
            service_name = repo["service_name"]
            will_pip_install = repo["will_pip_install"]
            break

    if not webhook_secret or not repo_path:
        log("Repository not found in config.json. Returning 400")
        return "Repository not found", 400

    # Verify the webhook secret
    mac = hmac.new(webhook_secret.encode(), msg=request.data, digestmod=hashlib.sha256)
    if not hmac.compare_digest(mac.hexdigest(), signature):
        log("Invalid Signature. Returning 400")
        return jsonify({"error": "Invalid signature"}), 400

    log("Webhook Validated")
    # Check if the push is to the master/main branch
    if not is_master_branch(request.json["ref"]):
        log("non Master/main Branch. Returning 200")
        return "OK", 200

    def task():
        run_command(command=f"sudo systemctl stop {service_name}", directory=repo_path)
        run_command(command="git stash", directory=repo_path)
        run_command(command="git pull", directory=repo_path)

        if will_pip_install:
            run_command(command="source activate", directory=repo_path)
            run_command(command="pip install -r requirements.txt", directory=repo_path)

        run_command(command=f"sudo systemctl start {service_name}", directory=repo_path)

    if repo_path in threads:
        threads[repo_path].join()

    threads[repo_path] = Thread(target=task)
    threads[repo_path].start()

    log("Webhook Processed Successfully - Returning 200")
    return "OK", 200
