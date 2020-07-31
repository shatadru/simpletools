#!/bin/bash
set -e
echo "Listing key.."
printf 'StorngPass123!\n'|bash -x ./otpgen/otpgen.sh -l


echo "Generating key for ID 1"
printf 'StorngPass123!\n'|time bash -x ./otpgen/otpgen.sh -g 1


echo "Generating key for ID 2"
printf 'StorngPass123!\n'|time bash -x ./otpgen/otpgen.sh -g 2
