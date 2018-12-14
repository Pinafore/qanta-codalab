import json
import argparse
import os
from os import path
import codecs

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure, savefig
import numpy as np

def list_codalab_bundles(root_dir):    
    return [dir for dir in os.listdir(root_dir) \
        if dir.endswith('-predict') and path.isdir(os.path.join(root_dir,dir))]

def aggregate_answers(root_dir,bundles):
    """
    load guesses and buzzes produced by all bundles for all questions
    """
    is_first = True
    all_responses = []
    bundle_to_ix = {}

    for ix, bundle in enumerate(bundles):
        bundle_to_ix[bundle] = ix
        with open(path.join(root_dir,bundle,'predictions.json')) as f:
            predictions = json.load(f)
        for qix, question in enumerate(predictions):
            if is_first:
                question_all_responses = []
            for pix, question_part in enumerate(question):
                if is_first:              
                    question_part_all_responses = question_part      
                    question_part_all_responses['buzzes'] \
                                        = [question_part['buzz']]
                    question_part_all_responses['guesses'] \
                                        = [question_part['guess']]

                    question_all_responses.append(question_part_all_responses)
                else:
                    t = all_responses[qix]
                    question_part_all_responses = t[pix]
                    question_part_all_responses['buzzes'].append(\
                                                question_part['buzz'])
                                 
                    question_part_all_responses['guesses'].append(\
                                                question_part['guess'])

            if is_first:
                all_responses.append(question_all_responses)
        is_first = False

    return all_responses, bundle_to_ix


def load_gold_answers(test_set_path):
    answers = {}
    with open(test_set_path) as inh:
        questions = json.load(inh)['questions']
    for qix, question in enumerate(questions):
        answers[qix] = question['page']

    return answers

def head_to_head(responses, bundle_to_ix, gold_answers, report_path):
    with open(report_path, 'w') as outh:
        bundles = list(bundle_to_ix.keys())
        for i, model_1 in enumerate(bundles):
            for model_2 in bundles[i+1:]:
                model_1_ix = bundle_to_ix[model_1]
                model_2_ix = bundle_to_ix[model_2]
                model_1_score = model_2_score = 0
                for question in responses:
                    gold_answer = gold_answers[question[0]['question_idx']]
                    for question_part in question:
                        buzz_1 = question_part['buzzes'][model_1_ix]
                        buzz_2 = question_part['buzzes'][model_2_ix]
                        guess_1 = question_part['guesses'][model_1_ix]
                        guess_2 = question_part['guesses'][model_2_ix]

                        if buzz_1 and guess_1 == gold_answer and \
                            buzz_2 and guess_2 == gold_answer:
                            #no-op
                            break                            
                        if buzz_1 and guess_1 != gold_answer and \
                            buzz_2 and guess_2 != gold_answer:
                            #no-op
                            break
                        if buzz_1:
                            if guess_1 == gold_answer:
                                model_1_score += 10
                                break
                            else:
                                last_guess_2 = \
                                    question[-1]['guesses'][model_2_ix]
                                if last_guess_2 == gold_answer:
                                    model_2_score += 10
                                break
                        if buzz_2:
                            if guess_2 == gold_answer:
                                model_2_score += 10
                                break
                            else:
                                last_guess_1 = \
                                    question[-1]['guesses'][model_1_ix]
                                if last_guess_1 == gold_answer:
                                    model_1_score += 10
                                break

                outh.write('{}\t{}\t{}\t{}\n'.format(\
                    model_1,model_1_score,model_2_score,model_2))


def remove_non_ascii(s): return "".join(i for i in s if ord(i)<128)

def buzz_ranking(responses, bundle_to_ix, gold_answers):
    bundles = list(bundle_to_ix.keys())
    models_buzz_ranking = [[]]*len(bundles)
    models_correct_buzz_ranking = [[]]*len(bundles)
    for question in responses:
        gold_answer = gold_answers[question[0]['question_idx']]
        already_buzzed = [False] * len(bundles)
        already_correct_buzzed = [False] * len(bundles)
        for position, question_part in enumerate(question):
            for model_ix, buzz in enumerate(question_part['buzzes']):
                if not already_buzzed[model_ix] and buzz:
                    models_buzz_ranking[model_ix].append(position)
                    already_buzzed[model_ix] = True

                if not already_correct_buzzed[model_ix] and buzz and \
                    question_part['guesses'][model_ix] == gold_answer:
                        models_correct_buzz_ranking[model_ix].append(position)
                        already_correct_buzzed[model_ix] = True


    return models_buzz_ranking, models_correct_buzz_ranking


def num_buzzes_per_position(responses, bundle_to_ix, gold_answers):
    bundles = list(bundle_to_ix.keys())
    buzzes_per_position = [] #each row is a question. Columns are positions.
    correct_buzzes_per_position = []
    cnt = 0
    for question in responses:
        gold_answer = gold_answers[question[0]['question_idx']]
        already_buzzed = [False] * len(bundles)
        already_correct_buzzed = [False] * len(bundles)
        question_buzzes = []
        question_correct_buzzes = []
        for position, question_part in enumerate(question):
            num_buzzes = num_correct_buzzes = 0
            for model_ix, buzz in enumerate(question_part['buzzes']):
                if not already_buzzed[model_ix] and buzz:
                    num_buzzes += 1
                    already_buzzed[model_ix] = True

                if not already_correct_buzzed[model_ix] and buzz and \
                    question_part['guesses'][model_ix] == gold_answer:
                        num_correct_buzzes += 1
                        already_correct_buzzed[model_ix] = True

            question_buzzes.append(num_buzzes)
            question_correct_buzzes.append(num_correct_buzzes)
        buzzes_per_position.append(question_buzzes)
        correct_buzzes_per_position.append(question_correct_buzzes)

    return buzzes_per_position, correct_buzzes_per_position


def positions_num_buzzes_counts(buzzes_per_position,num_models):
    """
    Input is matrix of num. questions x num positions
    Output is matrix of positions x num buzzes
    """
    max_num_buzzes = num_models
    max_pos = max([len(a) for a in buzzes_per_position])
    

    pos_buzzes = np.zeros((max_pos,max_num_buzzes+1))

    for question in buzzes_per_position:
        for pos, buzzes in enumerate(question):
            pos_buzzes[pos][buzzes] += 1
    return pos_buzzes

def num_correct_per_question(responses, bundle_to_ix, gold_answers):
    """
    Look at the guess for the full question text
    """
    num_correct_guesses = []
    for question in responses:
        gold_answer = gold_answers[question[0]['question_idx']]
        num_correct_guesses.append(sum([1 if gold_answer==guess else 0 \
            for guess in question[-1]['guesses']]))
    return num_correct_guesses


def buzz_report(responses, bundle_to_ix, gold_answers, report_dir, \
        early_pos_thr=4, late_pos_thr=10, buzz_thr=0.6):
    #1. questions with early buzzes
    buzzes_per_position, correct_buzzes_per_position = \
        num_buzzes_per_position(responses, bundle_to_ix, gold_answers)
    num_models = len(bundle_to_ix)
    #threshold filtering
    with open(path.join(report_dir,'questions-with-lots-of-early-buzzes.tsv')\
        , 'w') as eouth:
        with open(path.join(report_dir,\
            'questions-with-lots-of-late-buzzes.tsv'), 'w') as louth:
            for qix, question in enumerate(buzzes_per_position):
                q_info = responses[qix][-1]
                if sum(question[:early_pos_thr]) >= num_models*buzz_thr:
                    eouth.write('{}\t{}\n'.format(q_info['question_idx'], \
                        remove_non_ascii(q_info['text'])))
                elif sum(question[late_pos_thr:]) >= num_models*buzz_thr:
                    louth.write('{}\t{}\n'.format(q_info['question_idx'], remove_non_ascii(q_info['text'])))

def guess_report(responses, bundle_to_ix, gold_answers, report_dir,\
         guess_thr=0.9):
    num_correct_guesses = \
        num_correct_per_question(responses, bundle_to_ix, gold_answers)
    sort_indexes = sorted(range(len(num_correct_guesses)), \
        key=lambda k: num_correct_guesses[k])
    num_models = len(bundle_to_ix)
    """
    Num. of correct models for each question.
    """
    with codecs.open(path.join(report_dir,\
        'percentage-correct-models-per-question.tsv'),'w', encoding='utf-8') \
        as outh:
        outh.write('Question-idx\tText\tCorrect%\n')
        for qix in sort_indexes:
            question = responses[qix][-1]
            correct_percentage = num_correct_guesses[qix]*100.0/num_models
            outh.write('{}\t{}\t{}\n'.format(\
                question['question_idx'],\
                remove_non_ascii(question['text']),\
                 correct_percentage))

    #histogram
    figure(1, figsize=(6, 6))
    plt.hist(num_correct_guesses, normed=False, bins=num_models)
    plt.xlabel('Num. models (out of {}) making correct predictions'.format(\
        num_models))
    plt.ylabel('Num. Questions')
    savefig(path.join(report_dir,'num-correct-models-per-question.pdf'))

    """
    Questions with more than --thr-- of the models are getting right.
    """

    with codecs.open(path.join(report_dir,\
        'questions-most-models-get-right.tsv'),'w', encoding='utf-8') as routh:
        with codecs.open(path.join(report_dir,\
        'questions-most-models-get-wrong.tsv'),'w', encoding='utf-8') as wouth:
            wouth.write('Question-idx\tText\tCorrect%\n')
            routh.write('Question-idx\tText\tCorrect%\n')
            for qix in sort_indexes:
                question = responses[qix][-1]
                correct_percentage = float(num_correct_guesses[qix])/num_models

                if correct_percentage >= guess_thr:
                    routh.write('{}\t{}\t{}\n'.format(\
                        question['question_idx'],\
                        remove_non_ascii(question['text']),\
                         correct_percentage*100))
                elif correct_percentage <= 1- guess_thr:
                    wouth.write('{}\t{}\t{}\n'.format(\
                        question['question_idx'],\
                        remove_non_ascii(question['text']),\
                         correct_percentage*100))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('bundles_root_dir', type=str, default=None)
    parser.add_argument('test_set_path', type=str, default=None)
    parser.add_argument('report_output_dir', type=str, default=None)

    args = parser.parse_args()

    bundles = list_codalab_bundles(args.bundles_root_dir)
    gold_answers = load_gold_answers(args.test_set_path)
    print('Aggregating Answers ..')
    all_responses, bundle_to_ix = aggregate_answers(\
                args.bundles_root_dir,bundles)
    
    print('Head-to-Head Comparisions ..')
    head_to_head(all_responses, bundle_to_ix, gold_answers, \
        path.join(args.report_output_dir,'head-to-head.tsv'))
    
    print('Buzzing Report ..')
    buzz_report(all_responses, bundle_to_ix, gold_answers, \
            args.report_output_dir)
    
    print('Guessing Report ..')    
    guess_report(all_responses, bundle_to_ix, gold_answers, \
        args.report_output_dir)
    