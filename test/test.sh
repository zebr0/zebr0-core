#!/bin/sh -ex

# cleans a potentially failed previous test run
[ -f tmp/pid ] && kill "$(cat tmp/pid)"
[ -d tmp/ ] && rm -rf tmp/

# creates tmp directory
mkdir tmp

# starts the mock server
cd mock
python3 -m http.server &
echo $! > ../tmp/pid
sleep 1
cd ..

# zebr0 test 1: creating the parameter files
../src/zebr0 config -c tmp -u http://localhost:8000 -p dummy_project -s dummy_stage
diff tmp/url results/url
diff tmp/project results/project
diff tmp/stage results/stage

# zebr0 test 2: idempotence when reading from the parameter files
../src/zebr0 config -c tmp
diff tmp/url results/url
diff tmp/project results/project
diff tmp/stage results/stage

# lookup test 1: fetching the value of a key from the remote repository
../src/zebr0 get -c tmp test-key > tmp/test-key
diff tmp/test-key results/test-key

# lookup test 2: render
../src/zebr0 get -c tmp test-key --render > tmp/render
diff tmp/render results/render

# lookup test 3: strip
../src/zebr0 get -c tmp test-key --strip > tmp/strip
diff tmp/strip results/strip

# lookup test 4: project key
../src/zebr0 get -c tmp project-key > tmp/project-key
diff tmp/project-key results/project-key

# lookup test 5: stage key
../src/zebr0 get -c tmp stage-key > tmp/stage-key
diff tmp/stage-key results/stage-key

# lookup test 7: lookup filter
../src/zebr0 get -c tmp lookup --render > tmp/lookup
diff tmp/lookup results/render

# lookup test 10: default value
../src/zebr0 get -c tmp unknown-key --default "default value" > tmp/default
diff tmp/default results/default

# lookup test 11: default value in lookup filter
../src/zebr0 get -c tmp default --render > tmp/default2
diff tmp/default2 results/default

# stops the mock server
kill "$(cat tmp/pid)" && rm tmp/pid

# cleans tmp directory
rm -rf tmp
