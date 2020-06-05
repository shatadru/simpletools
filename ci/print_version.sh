#!/bin/bash
set -e
bash ./ci/display_env.sh || traue
time bash ./otpgen/otpgen.sh -V
