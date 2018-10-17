#!/usr/bin/env bash

# Codalab makes bundles write only
# So we copy everything into the write place
# Similar to how we have docker-compose setup
mkdir run
mkdir run/data

cp -RL src/* run
cp evaluate.py run/evaluate.py
cp curve_pipeline.pkl run/curve_pipeline.pkl
cp qanta.dev.2018.04.18.json run/data/qanta.dev.2018.04.18.json

# Run the evaluation
cd run
bash run.sh &
WEB_PID=$!
python evaluate.py data/qanta.dev.2018.04.18.json --char_step_size 200 --norun-web --wait 5
kill $WEB_PID

# Copy outputs so that codalab can pull it out of the container
cp scores.json ..
cp predictions.json ..
cp evaluation.log ..

# Be nice and cleanup
cd ..
rm -rf run

