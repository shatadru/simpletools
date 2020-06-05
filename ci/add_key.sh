#!/bin/bash
set -e

echo "Downloading sample HOTP image"
wget https://shatadru.in/runner_files/hotp_1.png || echo "echo Downloading resources failed"

echo "Downloading sample TOTP image"
wget https://shatadru.in/runner_files/totp_1.png || echo "echo Downloading resources failed"

echo "Listing key.."
time bash -x ./otpgen/otpgen.sh -l


echo "Adding HOTP key from image"
time bash -x ./otpgen/otpgen.sh -a hotp_1.png 
./otpgen/otpgen.sh -l


echo "Adding TOTP key from image"
time bash -x ./otpgen/otpgen.sh -a totp_1.png 
./otpgen/otpgen.sh -l

