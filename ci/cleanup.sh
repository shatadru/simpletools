#!/bin/bash
set -x 
echo "Removing old instalation"
sudo rm -rf $HOME/otpgen

echo "Removing previously downloaded images"
sudo rm -rf ./*.png
