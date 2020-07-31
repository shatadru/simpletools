#!/bin/bash
set -e
printf 'Y\nStorngPass123!\nStorngPass123!\n'|   sudo bash -x ./otpgen/otpgen.sh --clean-install
