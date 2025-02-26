#!/bin/bash
max_attempts=5
attempt_num=1
success=false
while [ $success = false ] && [ $attempt_num -le $max_attempts ]; do
  sudo dnf install -y git docker
  if [ $? -eq 0 ]; then
    echo "dnf install succeeded"
    success=true
  else
    echo "dnf install $attempt_num failed. trying again..."
    sleep 3
    ((attempt_num++))
  fi
done

sudo systemctl start docker
sudo gpasswd -a ec2-user docker
sudo gpasswd -a ssm-user docker
sudo chgrp docker /var/run/docker.sock
sudo service docker restart
sudo systemctl enable docker
sudo curl -L "https://github.com/docker/compose/releases/download/v2.28.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
cd /opt
sudo git clone https://github.com/langgenius/dify.git
cd /opt/dify
sudo git checkout 0.9.1-fix1
sudo git pull origin 0.9.1-fix1
cd /opt/dify/docker
sudo cp .env.example .env
docker-compose up -d 