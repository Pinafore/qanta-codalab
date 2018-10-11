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
def run(code, input_dir, output_dir):
    web_proc = subprocess.Popen(['python', '-m', code, 'web'],
                                preexec_fn=os.setsid,
                                stdout=subprocess.PIPE
                                )
    output = ''
    while 'Debug mode' not in output:
        output = web_proc.stdout.readline().decode('utf-8')
        # print('#', output)

    questions = json.load(open(input_dir))['questions']
    url = 'http://0.0.0.0:4861/api/1.0/quizbowl/act'
    results = {}
    for q in questions[:10]:
        answers = {}
        for char_index in range(0, len(q['text']), 25):
            text = q['text'][:char_index]
            resp = requests.post(url, data={'text': text})
            answers[char_index] = json.loads(resp.content.decode('utf-8'))
        results[q['qanta_id']] = answers

    with open(output_dir, 'w') as f:
        json.dump(results, f)

    os.killpg(os.getpgid(web_proc.pid), signal.SIGTERM)


if __name__ == '__main__':
    run()
