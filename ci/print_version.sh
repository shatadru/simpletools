#!/bin/bash
set -e
bash ./ci/display_env.sh || true
time bash ./otpgen/otpgen.sh -V
