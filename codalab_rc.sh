#!/usr/bin/env bash

# Codalab makes bundles write only
# So we copy everything into the write place
# Similar to how we have docker-compose setup
mkdir web
cp -RL src/* web
cd web

# Its easier to start the web API from bash and get proper logging
bash run.sh &
WEB_PID=$!
cd ..

# Run the evaluation, then cleanup
python evaluate.py --char_step_size 60 --norun-web --wait 5 --curve-pkl curve_pipeline.pkl qanta.dev.paragraphs.2018.04.18.json
kill $WEB_PID
rm -rf web

