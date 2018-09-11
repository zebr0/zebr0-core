#!/bin/sh -ex

# cleans a potentially failed previous test run
[ -d tmp/ ] && rm -rf tmp/

# creates tmp directory
mkdir tmp

# first test: creating the parameter files
../src/zebr0-init -c tmp -u https://raw.githubusercontent.com/zebr0/zebr0-conf/master -p dummy_project -s dummy_stage
diff tmp/url results/url
diff tmp/project results/project
diff tmp/stage results/stage

# second test: idempotence when reading from the parameter files
../src/zebr0-init -c tmp
diff tmp/url results/url
diff tmp/project results/project
diff tmp/stage results/stage

# third test: fetching the value of a key from the remote repository
../src/zebr0-lookup -c tmp LICENSE > tmp/LICENSE
diff tmp/LICENSE ../LICENSE

# cleans tmp directory
rm -rf tmp
