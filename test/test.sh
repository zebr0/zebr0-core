#!/bin/sh -ex

# creates tmp directory
mkdir tmp

# first test: creating the parameter files
../src/zebr0-init -d tmp -u dummy_url -p dummy_project -s dummy_stage
diff tmp/url results/url
diff tmp/project results/project
diff tmp/stage results/stage

# second test: idempotence when reading from the parameter files
../src/zebr0-init -d tmp
diff tmp/url results/url
diff tmp/project results/project
diff tmp/stage results/stage

# cleans tmp directory
rm -rf tmp
