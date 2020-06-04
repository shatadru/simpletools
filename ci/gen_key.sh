#!/bin/bash

echo "Listing key.."
bash -x ./otpgen/otpgen.sh -l


echo "Generating key for ID 1"
bash -x ./otpgen/otpgen.sh -g 1|| echo "Failed"


echo "Generating key for ID 2"

bash -x ./otpgen/otpgen.sh -g 2|| echo "Failed"
