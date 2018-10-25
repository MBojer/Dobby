#!/bin/bash

# https://gist.github.com/smoofit/dafa493aec8d41ea057370dbfde3f3fc
# sudo apt-get install libssl-dev
# sudo apt-get install libwebsockets-dev
# apt-get install uuid-dev



# Create User
sudo adduser dobby
# Give user sudo rights
sudo adduser dobby sudo
# For USB access
sudo adduser dobby dialout

# Set time
sudo date -s "$(wget -qSO- --max-redirect=0 google.com 2>&1 | grep Date: | cut -d' ' -f5-8)Z"

# Install dependencies
sudo apt-get install -y git mosquitto mosquitto-clients supervisor python-pip picocom mysql-server mysql-client default-libmysqlclient-dev

# Update pip
sudo pip install --upgrade pip

sudo pip install flask logging paho-mqtt psutil mysql-python

# Install dependencies - Dash
sudo pip install dash dash-html-components dash-core-components pandas dash-auth dash-table-experiments six


# Pull and move
git clone https://github.com/MBojer/Dobby.git
sudo mv Dobby /etc/Dobby

# Make Directories
sudo mkdir /var/log/Dobby/

# User rights
sudo chown -R dobby:dobby /etc/Dobby/
sudo chown -R dobby:dobby /var/log/Dobby/

# Sudo Rights
sudo cp /etc/Dobby/Install/Config_Files/sudoers.d/010_dobby-nopasswd /etc/sudoers.d/010_dobby-nopasswd

# RUN BELOW SQL SCRIP
MySQL_Setup.sql

# Supervisor Config
sudo ln -s /etc/Dobby/Install/Config_Files/supervisor/conf.d/Dobby.conf /etc/supervisor/conf.d/Dobby.conf
sudo ln -s /etc/Dobby/Install/Config_Files/supervisor/conf.d/Dash.conf /etc/supervisor/conf.d/Dash.conf
sudo supervisorctl reread
sudo supervisorctl update

# mosquitto Config
sudo ln -s /etc/Dobby/Install/Config_Files/mosquitto/Dobby_Auto.conf /etc/mosquitto/conf.d/Dobby_Auto.conf
