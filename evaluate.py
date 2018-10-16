import os
import json
import time
import click
import pickle
import signal
import requests
import subprocess
import numpy as np
import logging
from tqdm import tqdm


elog = logging.getLogger('eval')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('evaluation.log')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)


class CurveScore:
    def __init__(self, curve_pkl='../curve_pipeline.pkl'):
        with open(curve_pkl, 'rb') as f:
            self.pipeline = pickle.load(f)

    def get_weight(self, x):
        return self.pipeline.predict(np.asarray([[x]]))[0]

    def score(self, guesses, question):
        '''guesses is a list of {'guess': GUESS, 'buzz': True/False}
        '''
        char_length = len(question['text'])
        buzzes = [x['buzz'] for x in guesses]
        if True not in buzzes:
            return 0
        buzz_index = buzzes.index(True)
        rel_position = guesses[buzz_index]['char_index'] / char_length
        weight = self.get_weight(rel_position)
        result = guesses[buzz_index]['guess'] == question['page']
        return weight * result


def start_server():
    web_proc = subprocess.Popen(
        'bash run.sh', shell=True,
        preexec_fn=os.setsid
    )
    return web_proc


def retry_get_url(url, retries=5, delay=3):
    while retries > 0:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.ConnectionError as e:
            retries -= 1
            elog.warn(e)

        if delay > 0:
            time.sleep(delay)
    return None


def get_answer_single(url, questions, elog, char_step_size):
    elog.info('Collecting responses to questions')
    answers = []
    for question_idx, q in enumerate(tqdm(questions)):
        elog.info(f'Running question_idx={question_idx} qnum={q["qanta_id"]}')
        answers.append([])
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
                resp = requests.post(url, json=query).json()
                query.update(resp)
                answers[-1].append(query)
    return answers


def get_answer_batch(url, questions, elog, batch_size):
    elog.info('Collecting responses to questions in batches', batch_size)
    answers = []
    batch_ids = list(range(0, len(questions), batch_size))
    for batch_idx in tqdm(batch_ids):
        qs = questions[batch_idx: batch_idx + batch_size]
        answers.append([] for _ in qs)
        # TODO I don't think it's possible to batch if we do this
        sent_tokenizations = [q['tokenizations'] for q in qs]
        for sent_idx, (sent_st, sent_ed) in enumerate(sent_tokenizations):
            for char_idx in range(sent_st, sent_ed, char_step_size):
                query = {
                    'question_idx': question_idx,
                    'sent_index': sent_idx,
                    'char_index': char_idx,
                    'text': q['text'][:char_idx]
                }
                resp = requests.post(url, json=query).json()
                query.update(resp)
                answers[-1].append(query)
    return answers


@click.command()
@click.argument('input_dir')
@click.argument('output_dir', default='../predictions.json')
@click.argument('score_dir', default='../scores.json')
@click.option('--char_step_size', default=25)
@click.option('--hostname', default='0.0.0.0')
@click.option('--norun-web', default=False, is_flag=True)
@click.option('--wait', default=0, type=int)
@click.option('--curve-pkl', default='../curve_pipeline.pkl')
def evaluate(input_dir, output_dir, score_dir, char_step_size, hostname,
             norun_web, wait, curve_pkl):
    try:
        if not norun_web:
            web_proc = start_server()

        if wait > 0:
            time.sleep(wait)

        status_url = f'http://{hostname}:4861/api/1.0/quizbowl/status'
        status = retry_get_url(status_url)
        elog.info(f'API Status: {status}')
        if status is None:
            elog.warn('Failed to find a running web server beep boop. Something is probably about to have a RUD (rapid unscheduled disassembly)')
        else:
            print(status)

        url = f'http://{hostname}:4861/api/1.0/quizbowl/act'
        with open(input_dir) as f:
            questions = json.load(f)['questions']
        # if status['batch']:
        #     answers = get_answer_batch(url, questions, elog, char_step_size,
        #                                status['batch_size'])
        # else:
        #     answers = get_answer_single(url, questions, elog, char_step_size)
        answers = get_answer_single(url, questions, elog, char_step_size)

        with open(output_dir, 'w') as f:
            json.dump(answers, f)

        elog.info('Computing curve score of results')
        curve_score = CurveScore(curve_pkl=curve_pkl)
        curve_results = []
        eoq_results = []
        for question_idx, guesses in enumerate(answers):
            question = questions[question_idx]
            guess = guesses[-1]['guess']
            eoq_results.append(guess == question['page'])
            curve_results.append(curve_score.score(guesses, question))
        scores = {'eoq_acc': eoq_results, 'curve': curve_results}
        with open(score_dir, 'w') as f:
            json.dump(scores, f)
        eval_out = {
            'eoq_acc': sum(eoq_results) * 1.0 / len(eoq_results),
            'curve': sum(curve_results) * 1.0 / len(curve_results),
        }
        print(json.dumps(eval_out))

    finally:
        if not norun_web:
            os.killpg(os.getpgid(web_proc.pid), signal.SIGTERM)


if __name__ == '__main__':
    evaluate()
