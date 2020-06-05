#!/bin/bash
set -x
set -e

echo "Cleanup leftover from previous run"
sudo bash ./ci/cleanup.sh

echo "Adding execute permission"
chmod +x ./otpgen/otpgen.sh

