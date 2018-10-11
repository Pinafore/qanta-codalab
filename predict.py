import os
import json
import click
import signal
import requests
import subprocess
from qanta.tfidf import web
import logging

logging.getLogger("requests").setLevel(logging.WARNING)


def _web(input_dir):
    web()


@click.command()
@click.argument('code_dir')
@click.argument('input_dir')
@click.argument('output_dir')
@click.option('--char_step_size', default=25)
def predict(code_dir, input_dir, output_dir, char_step_size):
    '''start web service'''
    web_proc = subprocess.Popen(['python', '-m', code_dir, 'web'],
                                preexec_fn=os.setsid,
                                stdout=subprocess.PIPE
                                )
    output = ''
    while 'Debug mode' not in output:
        output = web_proc.stdout.readline().decode('utf-8')
        # print('#', output)

    '''get predictions'''
    url = 'http://0.0.0.0:4861/api/1.0/quizbowl/act'
    results = {}
    questions = json.load(open(input_dir))['questions']
    for q in questions[:10]:
        answers = {}
        # get an answer every K characters
        for char_index in range(0, len(q['text']), char_step_size):
            # this query defines the input to the models
            query = {
                'text': q['text'][:char_index],
                'qanta_id': q['qanta_id'],
                'char_index': char_index,
                'sent_index': 0,  # TODO
                # TODO extra stuff including game state
            }
            resp = requests.post(url, data=query)
            answers[char_index] = json.loads(resp.content.decode('utf-8'))
        results[q['qanta_id']] = answers

    with open(output_dir, 'w') as f:
        json.dump(results, f)

    os.killpg(os.getpgid(web_proc.pid), signal.SIGTERM)


if __name__ == '__main__':
    predict()
