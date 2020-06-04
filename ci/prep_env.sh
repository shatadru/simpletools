#!/bin/bash
set -x
set -e

echo "Cleanup leftover from previous run"
sudo bash ./ci/cleanup.sh

echo "Downloading sample HOTP image"
wget https://shatadru.in/runner_files/hotp_1.png || echo "echo Downloading resources failed"

echo "Downloading sample TOTP image"
wget https://shatadru.in/runner_files/totp_1.png || echo "echo Downloading resources failed"

echo "Adding execute permission"
chmod +x ./otpgen/otpgen.sh

