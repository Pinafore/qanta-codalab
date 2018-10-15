import os
import json
import click
import pickle
import signal
import requests
import subprocess
import numpy as np
import logging

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class CurveScore:

    def __init__(self):
        with open('../curve_pipeline.pkl', 'rb') as f:
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


@click.command()
@click.argument('input_dir')
@click.argument('n_questions', default=-1)
@click.option('--char_step_size', default=25)
@click.option('--hostname', default='0.0.0.0')
@click.argument('output_dir', default='predictions.json')
@click.argument('score_dir', default='scores.json')
def evaluate(input_dir,  n_questions, hostname, char_step_size,
             output_dir, score_dir):
    web_proc = subprocess.Popen(
        'bash run.sh', shell=True,
        # ['python', '-m', code_dir, 'web'],
        preexec_fn=os.setsid,
        stdout=subprocess.PIPE)
    output = ''
    while 'Debug mode' not in output:
        output = web_proc.stdout.readline().decode('utf-8')

    url = f'http://{hostname}:4861/api/1.0/quizbowl/act'
    answers = []
    questions = json.load(open(input_dir))['questions']
    if n_questions > 0:
        questions = questions[:n_questions]
    for question_idx, q in enumerate(questions):
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
                resp = requests.post(url, data=query).content.decode('utf-8')
                query.update(json.loads(resp))
                answers[-1].append(query)

    with open(output_dir, 'w') as f:
        json.dump(answers, f)

    os.killpg(os.getpgid(web_proc.pid), signal.SIGTERM)

    curve_score = CurveScore()
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


if __name__ == '__main__':
    evaluate()
