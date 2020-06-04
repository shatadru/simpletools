#!/bin/bash
set -e

echo "Listing key.."
time bash -x ./otpgen/otpgen.sh -l


echo "Adding HOTP key from image"
time bash -x ./otpgen/otpgen.sh -a hotp_1.png 
./otpgen/otpgen.sh -l


echo "Adding TOTP key from image"
time bash -x ./otpgen/otpgen.sh -a totp_1.png 
./otpgen/otpgen.sh -l

