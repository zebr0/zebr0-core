#!/bin/sh -ex

# cleans a potentially failed previous test run
[ -f tmp/pid ] && kill $(cat tmp/pid)
[ -d tmp/ ] && rm -rf tmp/

# creates tmp directory
mkdir tmp

# starts the mock server
cd mock
python3 -m http.server &
echo $! > ../tmp/pid
sleep 1
cd ..

# zebr0-init test 1: creating the parameter files
../src/zebr0-init -c tmp -u http://localhost:8000 -p dummy_project -s dummy_stage -v none
diff tmp/url results/url
diff tmp/project results/project
diff tmp/stage results/stage
diff tmp/vm results/vm

# zebr0-init test 2: idempotence when reading from the parameter files
../src/zebr0-init -c tmp
diff tmp/url results/url
diff tmp/project results/project
diff tmp/stage results/stage
diff tmp/vm results/vm

# lookup test 1: fetching the value of a key from the remote repository
../src/zebr0-lookup -c tmp test-key > tmp/test-key
diff tmp/test-key results/test-key

# lookup test 2: render
../src/zebr0-lookup -c tmp test-key --render > tmp/render
diff tmp/render results/render

# lookup test 3: strip
../src/zebr0-lookup -c tmp test-key --strip > tmp/strip
diff tmp/strip results/strip

# lookup test 4: project key
../src/zebr0-lookup -c tmp project-key > tmp/project-key
diff tmp/project-key results/project-key

# lookup test 5: stage key
../src/zebr0-lookup -c tmp stage-key > tmp/stage-key
diff tmp/stage-key results/stage-key

# lookup test 6: json filter
../src/zebr0-lookup -c tmp json --render > tmp/json
diff tmp/json results/json

# lookup test 7: lookup filter
../src/zebr0-lookup -c tmp lookup --render > tmp/lookup
diff tmp/lookup results/render

# lookup test 8: sh filter
../src/zebr0-lookup -c tmp sh --render > tmp/sh
diff tmp/sh results/sh

# lookup test 9: hash filter
../src/zebr0-lookup -c tmp hash --render > tmp/hash
diff tmp/hash results/hash

# lookup test 10: default value
../src/zebr0-lookup -c tmp unknown-key --default "default value" > tmp/default
diff tmp/default results/default

# lookup test 11: default value in lookup filter
../src/zebr0-lookup -c tmp default --render > tmp/default2
diff tmp/default2 results/default

# zebr0-template test
cat mock/test-key | ../src/zebr0-template -c tmp > tmp/template
diff tmp/template results/template

# stops the mock server
kill $(cat tmp/pid) && rm tmp/pid

# cleans tmp directory
rm -rf tmp
