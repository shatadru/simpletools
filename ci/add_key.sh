#!/bin/bash
set -e

echo "Downloading sample HOTP image"
wget https://shatadru.in/runner_files/hotp_1.png || echo "echo Downloading resources failed"

echo "Downloading sample TOTP image"
wget https://shatadru.in/runner_files/totp_1.png || echo "echo Downloading resources failed"

echo "Listing key.."
time  printf 'StorngPass123!\n' |bash -x ./otpgen/otpgen.sh -l


echo "Adding HOTP key from image"
time  printf 'StorngPass123!\n' | bash -x ./otpgen/otpgen.sh -a hotp_1.png 
printf 'StorngPass123!\n' |./otpgen/otpgen.sh -l


echo "Adding TOTP key from image"
time  printf 'StorngPass123!\n' | bash -x ./otpgen/otpgen.sh -a totp_1.png 
printf 'StorngPass123!\n' | ./otpgen/otpgen.sh -l

