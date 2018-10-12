import os
import json
import click
import signal
import requests
import subprocess
from qanta.tfidf import web


def _web(input_dir):
    web()


@click.command()
@click.argument('code_dir')
@click.argument('input_dir')
@click.argument('output_dir')
@click.argument('score_dir')
@click.option('--char_step_size', default=25)
def predict(code_dir, input_dir, output_dir, score_dir, char_step_size):
    web_proc = subprocess.Popen(['python', '-m', code_dir, 'web'],
                                preexec_fn=os.setsid,
                                stdout=subprocess.PIPE)
    output = ''
    while 'Debug mode' not in output:
        output = web_proc.stdout.readline().decode('utf-8')

    url = 'http://0.0.0.0:4861/api/1.0/quizbowl/act'
    results = []
    questions = json.load(open(input_dir))['questions']
    for question_idx, q in enumerate(questions[:10]):
        results.append([])
        sent_tokenizations = q['tokenizations']
        # get an answer every K characters
        for sent_idx, (sent_st, sent_ed) in enumerate(sent_tokenizations):
            for char_idx in range(sent_st, sent_ed, char_step_size):
                query = {
                    'question_idx': question_idx,
                    'sent_index': sent_idx,
                    'char_index': char_idx,
                    'text': q['text'][:char_idx]
                }
                resp = requests.post(url, data=query).content.decode('utf-8')
                query.update(json.loads(resp))
                results[-1].append(query)

    with open(output_dir, 'w') as f:
        json.dump(results, f)

    os.killpg(os.getpgid(web_proc.pid), signal.SIGTERM)


if __name__ == '__main__':
    predict()
