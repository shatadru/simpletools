#!/bin/bash
set -e

echo "Listing key.."
time  printf 'StorngPass123!\n' |bash -x ./otpgen/otpgen.sh -l


echo "Removing TOTP 2FA"
time  printf 'StorngPass123!\n' | bash -x ./otpgen/otpgen.sh -r 2 
printf 'StorngPass123!\n' |./otpgen/otpgen.sh -l


echo "Removing HOTP 2FA"
time  printf 'StorngPass123!\n' | bash -x ./otpgen/otpgen.sh -r 1
printf 'StorngPass123!\n' | ./otpgen/otpgen.sh -l

