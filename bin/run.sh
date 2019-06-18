#!/usr/bin/env bash

# Start MongoDB if not already running
if ! pgrep mongod > /dev/null ; then
   mongod --dbpath ./results --logpath ./results/log/mongodb.log > /dev/null &
fi

python3 bin/parse_instances.py

num_benches=1
if [[ $# -eq 1 && $1 -gt 1 ]]; then
   num_benches=$1
fi

for ((n=0;n<${num_benches};n++)); do
   python3 bin/bench.py
done

python3 bin/analyze.py

# Kill MongoDB if running
if pgrep mongod > /dev/null ; then
   mongo_process=$(pgrep mongod)
   kill ${mongo_process}
fi