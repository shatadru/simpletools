#!/bin/bash
set -x 
HOME=$(bash <<< "echo ~${SUDO_USER:-}")
export HOME

echo "Removing old instalation"
sudo rm -rf "$HOME"/otpgen

echo "Removing previously downloaded images"
sudo rm -rf ./*.png
