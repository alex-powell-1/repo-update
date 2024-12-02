SERVICE_NAME="repo-update.service"

sudo systemctl stop $SERVICE_NAME
git stash
git pull
source activate
pip install -r requirements.txt
sudo systemctl start $SERVICE_NAME