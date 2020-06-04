#!/bin/bash
set -e
echo "Listing key.."
bash -x ./otpgen/otpgen.sh -l


echo "Generating key for ID 1"
time bash -x ./otpgen/otpgen.sh -g 1


echo "Generating key for ID 2"

time bash -x ./otpgen/otpgen.sh -g 2
