#!/bin/bash

# Static IP example
# interface eth0
#
# static ip_address=192.168.0.2/24
# static routers=192.168.0.1
# static domain_name_servers=192.168.0.1
#
# interface wlan0
#
# static ip_address=192.168.0.2/24
# static routers=192.168.0.1
# static domain_name_servers=192.168.0.1

# https://community.plot.ly/t/get-username-for-authenticated-user-with-dash-basic-auth/6450/3
# File to change: /usr/local/lib/python2.7/dist-packages/dash_auth/basic_auth.py
# NOTE: Add below just after "if pair[0] == username and pair[1] == password:"
# self._username = username
# To get username option from basic_auth

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
yes | sudo pip install --upgrade pip

yes | sudo pip install flask logging paho-mqtt psutil mysql-python gitpython

# Install dependencies - Dash
yes | sudo pip install dash dash-html-components dash-core-components pandas dash-auth dash-table-experiments six

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
sudo mysql < /etc/Dobby/Install/MySQL_Setup.sql

# Supervisor Config
sudo ln -s /etc/Dobby/Install/Config_Files/supervisor/conf.d/Dobby.conf /etc/supervisor/conf.d/Dobby.conf
sudo ln -s /etc/Dobby/Install/Config_Files/supervisor/conf.d/Dash.conf /etc/supervisor/conf.d/Dash.conf
sudo supervisorctl reread
sudo supervisorctl update

# mosquitto Config
sudo ln -s /etc/Dobby/Install/Config_Files/mosquitto/Dobby_Auto.conf /etc/mosquitto/conf.d/Dobby_Auto.conf
