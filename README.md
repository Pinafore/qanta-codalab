# Installation

You will only need to have [docker](https://docker.com) and `docker-compose` installed to run this reference system.

# Example Docker Containers

We provide an example [docker](http://docker.com) container for answering
Quiz Bowl questions. The container runs a simple system
that consists of a TF-IDF guesser and a threshold-based buzzer.
The input unit to the system is a question (sequence of words)
and the system outputs an answer guess (a Wikipedia entity)
and a binary decision whether to buzz or not.
Participating systems should adhere to the input/output format
described later.


We provide two methods for interacting with the docker
container—**Batch container** and **HTTP service container**.
In the batch mode, the container is run for a given input
file that consists of multiple questions, one question per line.
The container produces an output file that consists of answers
to each of the given questions. The HTTP service container
starts a background service that processes POST requests
(submitted for example using a Curl command), where each
request is an individual question. The HTTP service container
is more suitable for the incremental question answering setup
(e.g., when questions are provided word-by-word).


## Download a pre-trained baseline model
Building the docker images requires having a pre-trained
TF-IDF model stored under `./tfidf_model/`.
A pre-trained model can be downloaded using [this link](https://drive.google.com/file/d/1nqMPaMxnygGEz_VF1CoMK9XYQawl9Nov/view?usp=sharing). The script we used to train
that model is `train_tfidf_model.sh`.


## Building Docker Images
The instructions below assumes that docker is installed on
the host machine. Installation instructions can be found
at [docker documentation](https://docs.docker.com/docker-for-mac/install/).

We provide docker files for building images of the batch
and the HTTP service containers. The following commands
can be used to build the images

  	docker build -f Baseline_Batch.DockerFile -t='qa_baseline_batch' .
  	docker build -f Baseline_HTTP.DockerFile -t='qa_baseline_http' .

where the docker files `Baseline_Batch.DockerFile` and
`Baseline_HTTP.DockerFile` are used to generated docker images
with the names `qa_baseline_batch` and `qa_baseline_http`, respectively.
## Input/Output Formats
In both modes, each question should be formatted as a json object
the consists of the following fields:
 * `char_position` Character position of provided question text
 * `question_text` Question text up to `char_position`
 * `incremental_text` Incremental text from last position to current position
 * `tossup_number` question number
 * `sent_number` The current sentence number. (starting from 0 for the tokens in the first sentence of the questions)


#### Example Input

   	{"char_position":112, "question_text": "At its premiere, the librettist of this opera portrayed a character who asks for a glass of wine with his dying wish", "Incremental_text":"a glass of wine with his dying wish", "tossup_number": 1, "sent_number": 0}

The output answer to each question is also a json object of two fields
 * `guess` Guessed Wikipedia answer entity
 * `buzz` true/false whether to buzz given the seen question text so far or not

#### Example Output

  	{"guess": "The_Marriage_of_Figaro", "buzz": true}

## Running Containers

### Batch Mode
The following command can be used to run the batch container

  	docker run -v <path to data dir on host>:/app/data -t -i qa_baseline_batch <batch input file> <output file>

Three fields need to be provided for the command above
 * `<path to data dir on host>` A directory on the host machine that contains the input questions file `<batch input file>`
 * `<batch input file>` The name of the input file. Each line
    should be a question in the input format above. `sample_batch_input.jsonl` is an example input batch file.
 * `<output file>` The name of the generated output file. The file
    will be placed in `<path to data dir on host>`.

 For example, if your data is in `/home/qa-data` then use

  	 docker run -v /home/qb-data:/app/data -t -i qa_baseline_batch sample_batch_input.jsonl answers.jsonl


### HTTP Service Mode
The following command can be used to run the HTTP service container

  	docker run -p 8080:80 -t -i qa_baseline_http

The command above will start a container that answers questions each submitted as an HTTP request. `-p 8080:80`
maps port 8080 on the host machine to port 80 on the
container (on which we bind the question answering service).
For example, after starting the container, one can run
the following curl request on the host machine

  	curl -XPOST --header "Content-Type: application/json" -d '{"char_position":112, "question_text": "At its premiere, the librettist of this opera portrayed a character who asks for a glass of wine with his dying wish", "Incremental_text":"a glass of wine with his dying wish", "tossup_number": 1, "sent_number": 0 }' http://localhost:8080/qa

and gets a json response

  	{"guess": "The_Marriage_of_Figaro", "buzz": true}
