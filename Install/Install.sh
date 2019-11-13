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

# USB Driver for EP Ever charge controller Only tested with TracerA series
# NOTE: when the kernal is updated this driver stopps working
# cd /etc/Dobby/Install/xr_usb_serial_common-1a
# sudo make
# mkdir /lib/modules/$(uname -r)/extra
# sudo cp xr_usb_serial_common.ko /lib/modules/$(uname -r)/extra/


# Create User
sudo adduser dobby
# Give user sudo rights
sudo adduser dobby sudo
# For USB access
sudo adduser dobby dialout

# Set time
sudo date -s "$(wget -qSO- --max-redirect=0 google.com 2>&1 | grep Date: | cut -d' ' -f5-8)Z"

# Install dependencies
sudo apt-get install -y git mosquitto-clients python-pip picocom mysql-server mysql-client default-libmysqlclient-dev

# Update pip
yes | sudo pip install --upgrade pip

# Install Dependencies
yes | sudo pip install flask logging paho-mqtt psutil mysql-python gitpython schedule six pymodbus

# Install Dash
yes | sudo pip install dash==0.36.0 dash-html-components==0.13.5 dash-core-components==0.43.0 dash-auth==1.2.0 dash-table==3.1.11

# Pull and move
git clone https://github.com/MBojer/Dobby.git
sudo mv Dobby /etc/Dobby

# Make Directories
sudo mkdir /etc/Dobby/Backup/

# User rights
sudo chown -R dobby:dobby /etc/Dobby/

# Sudo Rights
sudo cp /etc/Dobby/Install/Config_Files/sudoers.d/010_dobby-nopasswd /etc/sudoers.d/010_dobby-nopasswd

# RUN BELOW SQL SCRIP
sudo mysql < /etc/Dobby/Install/MySQL_Setup.sql

# systemd config
## copy config files
sudo cp /etc/Dobby/Install/Config_Files/systemd/dobby.service /lib/systemd/system
sudo cp /etc/Dobby/Install/Config_Files/systemd/dobbydash.service /lib/systemd/system

# mosquitto Config
sudo ln -s /etc/Dobby/Install/Config_Files/mosquitto/Dobby_Auto.conf /etc/mosquitto/conf.d/Dobby_Auto.conf

# Create certificate for Dash
# https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
mkdir /etc/Dobby/Cert
mv cert.pem /etc/Dobby/Cert/
mv key.pem /etc/Dobby/Cert/

# Mosquitto
# Get mosquitto
git clone https://github.com/eclipse/mosquitto
cd mosquitto
# Gives errors but seems to work
make
# Change permissions
sudo chown mosquitto:mosquitto src/mosquitto
# copy exe
sudo copy src/mosquitto /usr/sbin/
# Add user
sudo useradd -M mosquitto
# then lock the account to prevent logging in
sudo usermod -L mosquitto
# Copy systemd service file
sudo cp /etc/Dobby/Install/Config_Files/systemd/mosquitto.service /lib/systemd/
# Make log dir
sudo mkdir /var/log/mosquitto
sudo chown -R mosquitto:mosquitto /var/log/mosquitto


# Set services to start on boot
## update deamons
sudo systemctl daemon-reload 
## Enable deamons on boot
sudo systemctl enable dobby
sudo systemctl enable dobbydash
sudo systemctl enable mosquitto
