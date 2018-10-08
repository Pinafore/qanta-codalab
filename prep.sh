#!/bin/bash

python dataset.py download --dataset qanta_full

mkdir tfidf_model

python train_model.py
