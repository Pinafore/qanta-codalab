import os
import time
import json
import click
import signal
import requests
import subprocess
import threading
from qanta.tfidf import web
import logging

# logging.getLogger("requests").setLevel(logging.WARNING)


def _web(input_file):
    web()


@click.command()
@click.argument('code')
@click.argument('input_file')
@click.argument('output_file')
def run(code, input_file, output_file):
    web_proc = subprocess.Popen(['python', '-m', code, 'web'],
                                # close_fds=True,
                                preexec_fn=os.setsid,
                                stdout=subprocess.PIPE
                                )
    output = ''
    while 'Debug mode' not in output:
        output = web_proc.stdout.readline().decode('utf-8')
        # print('#', output)

    questions = json.load(open(input_file))['questions']
    url = 'http://0.0.0.0:4861/api/1.0/quizbowl/act'
    results = {}
    for q in questions[:10]:
        resp = requests.post(url, data={'question_text': q['text']})
        results[q['qanta_id']] = json.loads(resp.content.decode('utf-8'))
    with open(output_file, 'w') as f:
        json.dump(results, f)

    os.killpg(os.getpgid(web_proc.pid), signal.SIGTERM)


if __name__ == '__main__':
    run()
