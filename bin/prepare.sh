#!/bin/bash

# CONFIG FILE LINKING:
# ---------------------
if [[ ! $# -eq 1 || ! -f $1 ]]; then
   echo "Please provide a valid config.json file"
   echo "Usage: ./prepare.sh [ABSOLUTE path to config.json]"
   exit 1
fi

if [[ -f bin/config.json ]]; then

   echo "WARNING: previous config file detected:"
   echo "Proceeding will overwrite existing image files."
   read -p "Do you want to continue? [Y/n] " response

   if [[ "${response}" = "Y" ]]; then
      echo "Now using new config file."

   else
      echo "Abandoning setup"
      exit 0
   fi

fi

ln -sf $1 bin/config.json


# MONGODB + MONGOENGINE SETUP:
# ---------------------
if [[ ! -d "results" ]]; then

   mkdir results

   sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 9DA31620334BD75D9DCB49F368818C72E52529D4

   version=$(lsb_release -r -s)  # Detects Ubuntu version to install correct version of MongoDB
   if [[ "${version}" = "16.04" ]]; then
      echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/4.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.0.list
   fi
   if [[ "${version}" = "18.04" ]]; then
      echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.0.list
   fi

   sudo apt-get update
   sudo apt-get install -y mongodb-org

   user="$(id -u -n)"
   sudo chown -R ${user} ./results

   pip install mongoengine
fi


# ANALYSIS TOOLS:
# ---------------------
if [[ ! -d "images" ]]; then

   mkdir images

   sudo apt install python3-pip
   pip3 install --upgrade pip
   pip3 install matplotlib
   pip3 install numpy

   sudo chown -R ${user} ./images
fi