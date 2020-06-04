#!/bin/bash

echo "Listing key.."
bash -x ./otpgen/otpgen.sh -l


echo "Adding HOTP key from image"
bash -x ./otpgen/otpgen.sh -a hotp_1.png && echo "HOTP key added" || echo "Failed"
./otpgen/otpgen.sh -l


echo "Adding TOTP key from image"
bash -x ./otpgen/otpgen.sh -a totp_1.png && echo "TOTP key added" || echo "Failed"
./otpgen/otpgen.sh -l

