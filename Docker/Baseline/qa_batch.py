import sys

import time
import json
from os import path
from argparse import ArgumentParser

from qanta.guesser.tfidf import TfidfGuesser

MODEL_SAVE_DIR = 'tfidf_model'
BUZZ_NUM_GUESSES = 10
BUZZ_THRESHOLD = 0.3
PROGRESS_RATE = 10
DATA_MOUNT_DIR = '/app/data'

def batch_qa(input_file, output_file):
    """
    params
        input_file: each line is a question in json format
            {"char_position":int, "question_text": str, "Incremental_text":str,"Is_new_sent":false/true}
        output_file: each line is a question in json format
            {"guess":str, "buzz": false/true}
    """
    tfidf_guesser = TfidfGuesser.load(MODEL_SAVE_DIR)
        
    def _guess(question_text):
        guesses = tfidf_guesser.guess([question_text],BUZZ_NUM_GUESSES)[0]
        scores = [guess[1] for guess in guesses]
        buzz = scores[0]/sum(scores) >= BUZZ_THRESHOLD
        return guesses[0][0], buzz

    progress = 0
    with open(path.join(DATA_MOUNT_DIR,output_file), 'w') as outh:
        with open(path.join(DATA_MOUNT_DIR,input_file)) as inh:
            for question_json in inh:
                guess, buzz = _guess(json.loads(question_json)['question_text'])
                outh.write(json.dumps({'guess': guess, 'buzz': True if buzz else False}) + '\n')
                progress += 1
                if progress % PROGRESS_RATE == 0: print('Processed {} questions.'.format(progress))

if __name__ == '__main__':

    parser = ArgumentParser()    
    parser.add_argument('input_file', help='path to input file')
    parser.add_argument('output_file', help='output file path')

    args = parser.parse_args()

    batch_qa(args.input_file, args.output_file)