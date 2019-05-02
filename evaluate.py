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
import socket
import errno
from tqdm import tqdm



elog = logging.getLogger('eval')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('evaluation.log')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)

logging.getLogger('requests').setLevel(logging.CRITICAL)


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
        rel_position = (1.0 * guesses[buzz_index]['char_index']) / char_length
        weight = self.get_weight(rel_position)
        result = guesses[buzz_index]['guess'] == question['page']
        return weight * result

    def score_optimal(self, guesses, question):
        '''score with an optimal buzzer'''
        char_length = len(question['text'])
        buzz_index = char_length
        for g in guesses[::-1]:
            if g['guess'] != question['page']:
                buzz_index = g['char_index']
                break
        rel_position = (1.0 * buzz_index) / char_length
        return self.get_weight(rel_position)


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


def get_question_query(qid, question, evidence, char_idx, wiki_paragraphs=False):
    char_idx = min(char_idx, len(question['text']))

    for sent_idx, (st, ed) in enumerate(question['tokenizations']):
        if char_idx >= st and char_idx <= ed:
            break

    query = {
            'question_idx': qid,
            'sent_index': sent_idx,
            'char_index': char_idx,
            'text': question['text'][:char_idx]
    }
    if wiki_paragraphs:
        evidences = evidence['sent_evidences'][:sent_idx+1]
        #evidences here is a list of lists of length = #sentences seen so far, and each sublist is contains 5 dictionaries for the 5 top sentences
        query['wiki_paragraphs'] = evidences
    return query



def get_answer_single(url, questions, evidences, char_step_size, wiki_paragraphs=False):
    elog.info('Collecting responses to questions')
    answers = []
    for question_idx, q in enumerate(tqdm(questions)):
        elog.info(f'Running question_idx={question_idx} qnum={q["qanta_id"]}')
        answers.append([])
        # get an answer every K characters
        if wiki_paragraphs:
            for char_idx in range(1, len(q['text']) + char_step_size,
                                  char_step_size):
                query = get_question_query(question_idx, q, evidences[question_idx], char_idx, wiki_paragraphs)
                resp = requests.post(url, json=query).json()
                query.update(resp)
                answers[-1].append(query)
        else:
            for char_idx in range(1, len(q['text']) + char_step_size,
                                  char_step_size):
                query = get_question_query(question_idx, q, [], char_idx, wiki_paragraphs)
                resp = requests.post(url, json=query).json()
                query.update(resp)
                answers[-1].append(query)    
    return answers


def get_answer_batch(url, questions, evidences, char_step_size, batch_size, wiki_paragraphs=False):
    elog.info('Collecting responses to questions in batches', batch_size)
    answers = []
    batch_ids = list(range(0, len(questions), batch_size))
    for batch_idx in tqdm(batch_ids):
        batch_ed = min(len(questions), batch_idx + batch_size)
        qs = questions[batch_idx: batch_ed]
        max_len = max(len(q['text']) for q in qs)
        qids = list(range(batch_idx, batch_ed))
        answers += [[] for _ in qs]
        if wiki_paragraphs:
            evs = evidences[batch_idx: batch_ed]
            for char_idx in range(1, max_len + char_step_size, char_step_size):
                query = {'questions': []}
                for i, q in enumerate(qs):
                    query['questions'].append(
                        get_question_query(qids[i], q, evs[i], char_idx, wiki_paragraphs))
                resp = requests.post(url, json=query).json()
                for i, r in enumerate(resp):
                    q = query['questions'][i]
                    q.update(r)
                    answers[qids[i]].append(q)
        else:
           for char_idx in range(1, max_len + char_step_size, char_step_size):
                query = {'questions': []}
                for i, q in enumerate(qs):
                    query['questions'].append(
                        get_question_query(qids[i], q, [], char_idx, wiki_paragraphs))
                resp = requests.post(url, json=query).json()
                for i, r in enumerate(resp):
                    q = query['questions'][i]
                    q.update(r)
                    answers[qids[i]].append(q)
    return answers


def check_port(hostname, port):
    pass


@click.command()
@click.argument('input_dir')
#@click.argument('evidence_dir', default='data/evidence_docs_dev_with_sent_text.json')
@click.argument('output_dir', default='predictions.json')
@click.argument('score_dir', default='scores.json')
@click.option('--char_step_size', default=25)
@click.option('--hostname', default='0.0.0.0')
@click.option('--norun-web', default=False, is_flag=True)
@click.option('--wait', default=0, type=int)
@click.option('--curve-pkl', default='curve_pipeline.pkl')
@click.option('--retries', default=20)
@click.option('--retry-delay', default=3)
def evaluate(input_dir, output_dir, score_dir, char_step_size, hostname,
             norun_web, wait, curve_pkl, retries, retry_delay):
    try:
        if not norun_web:
            web_proc = start_server()

        if wait > 0:
            time.sleep(wait)

        status_url = f'http://{hostname}:4861/api/1.0/quizbowl/status'
        status = retry_get_url(status_url, retries=retries, delay=retry_delay)
        elog.info(f'API Status: {status}')
        if status is None:
            elog.warning('Failed to find a running web server beep boop, prepare for RUD')
            raise ValueError('Status API could not be reached')

        if 'include_wiki_paragraphs' in status:
            include_wiki_paragraphs = status['include_wiki_paragraphs']
        else:
            include_wiki_paragraphs = False

        with open(input_dir) as f:
            questions = json.load(f)['questions']
                  
        evidences = []
        if include_wiki_paragraphs:
            evidence_dir = 'data/evidence_docs_dev_with_sent_text.json'
            with open(evidence_dir) as f:
                evidences = json.load(f)['evidence']

        if status is not None and status['batch'] is True:
            url = f'http://{hostname}:4861/api/1.0/quizbowl/batch_act'
            answers = get_answer_batch(url, questions, evidences,
                                       char_step_size,
                                       status['batch_size'],
                                       wiki_paragraphs=include_wiki_paragraphs)
        else:
            url = f'http://{hostname}:4861/api/1.0/quizbowl/act'
            answers = get_answer_single(url, questions, evidences,
                                        char_step_size,
                                        wiki_paragraphs=include_wiki_paragraphs)

        with open(output_dir, 'w') as f:
            json.dump(answers, f)

        elog.info('Computing curve score of results')
        curve_score = CurveScore(curve_pkl=curve_pkl)
        first_acc = []
        end_acc = []
        ew = []
        ew_opt = []

        for question_idx, guesses in enumerate(answers):
            question = questions[question_idx]
            answer = question['page']
            first_guess = None
            for g in guesses:
                if g['sent_index'] == 1:
                    first_guess = g['guess']
                    break
            first_acc.append(first_guess == answer)
            end_acc.append(guesses[-1]['guess'] == answer)
            ew.append(curve_score.score(guesses, question))
            ew_opt.append(curve_score.score_optimal(guesses, question))
        eval_out = {
            'first_acc': sum(first_acc) * 1.0 / len(first_acc),
            'end_acc': sum(end_acc) * 1.0 / len(end_acc),
            'expected_wins': sum(ew) * 1.0 / len(ew),
            'expected_wins_optimal': sum(ew_opt) * 1.0 / len(ew_opt),
        }
        with open(score_dir, 'w') as f:
            json.dump(eval_out, f)
        print(json.dumps(eval_out))

    finally:
        if not norun_web:
            os.killpg(os.getpgid(web_proc.pid), signal.SIGTERM)


if __name__ == '__main__':
    evaluate()
