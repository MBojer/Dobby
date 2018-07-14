#!/bin/bash

# Make User
sudo adduser dobby sudo
## For USB access
sudo adduser dobby dialout

# Install dependencies
sudo apt-get install -y git mosquitto mosquitto-clients supervisor python-pip picocom mysql-server mysql-client default-libmysqlclient-dev

pip install flask logging paho-mqtt psutil mysql-python

# Pull and move
git clone https://github.com/MBojer/DobbyShell.git
sudo mv DobbyShell /etc/Dobby

# Make Directories
sudo mkdir /var/log/Dobby/
sudo mkdir /var/log/Dobby/Output/
sudo mkdir /var/log/Dobby/Error/

sudo mkdir /var/log/Dobby/Web_db
sudo mkdir /var/log/Dobby/Web_db/Output/
sudo mkdir /var/log/Dobby/Web_db/Error/

# User rights
sudo chown -R dobby:dobby /etc/Dobby/
sudo chown -R dobby:dobby /var/log/Dobby/

# Sudo Rights
sudo cp /etc/Dobby/Install/Config_Files/sudoers.d/010_dobby-nopasswd /etc/sudoers.d/010_dobby-nopasswd

# Supervisor Config
sudo ln -s /etc/Dobby/Install/Config_Files/supervisor/conf.d/Dobby.conf /etc/supervisor/conf.d/Dobby.conf
sudo supervisorctl reread
sudo supervisorctl update
