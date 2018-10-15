import subprocess
import json
import os
import argparse
import sys



def main():
	parser = argparse.ArgumentParser('Evaluation script for QANTA.')
	parser.add_argument('data_file', metavar='data.json', help='Input data JSON file.')
	parser.add_argument('gold_file', metavar='gold.json', help='Model predictions.')
	if len(sys.argv) < 2:
		parser.print_help()
		sys.exit(1)

	args = parser.parse_args()
	gold_ans_list = list()
	pred_ans_list = list()
	count = 0
	os.system("docker-compose up &")
	with open(args.data_file) as f:
		for line in f:
			question_text = json.loads(line)['question_text']
			command = "http --form POST http://0.0.0.0:4861/api/1.0/quizbowl/act text='" + question_text + "'" + ">./data/output.jsonl"
			os.system(command)
			with open('./data/output.jsonl') as f1:
				for line in f1:
					pred_ans_list.append(json.loads(line)['guess'])


	with open(args.gold_file) as f2:
		for line in f2:
			gold_ans = json.loads(line)['label']
			gold_ans_list.append(gold_ans)
	for i in range(len(gold_ans_list)):
		if gold_ans_list[i] == pred_ans_list[i]:
			count += 1
	print(count / len(gold_ans_list))
	os.system('rm ./data/output.jsonl')






if __name__ == '__main__':
    main()

