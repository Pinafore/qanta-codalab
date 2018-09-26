# Example Docker Containers

We provide an example docker container for answering
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


## Training a baseline model
Building the docker images requires having a pre-trained
TF-IDF model. `./prep.sh` can be used to download Quiz Bowl
training set and train a model. The model is stored in `./tfidf_model`.

## Building Docker Images

We provide docker files for building images of the batch
and the HTTP service containers. The following commands
can be used to build the images

  	docker build -f Baseline_Batch.DockerFile -t='qa_baseline_batch' .
  	docker build -f Baseline_HTTP.DockerFile -t='qa_baseline_http' .


## Input/Output Formats
In both modes, each question should be formatted as a json object
the consists of the following fields:
 * `char_position` Character position of provided question text
 * `question_text` Question text up to `char_position`
 * `incremental_text` Incremental text from last position to current position
 * `Is_new_sent` true/false is `incremental_text` a new sentence

#### Example Input

  	{"char_position":112, "question_text": "At its premiere, the librettist of this opera portrayed a character who asks for a glass of wine with his dying wish", "Incremental_text":"a glass of wine with his dying wish","Is_new_sent":false }

 Index (character position)
Question text up to this position
Incremental text from last position to current position Is_new_sent

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
    should be a question in the input format above. `sample_batch_input.txt` is an example input batch file.
 * `<output file>` The name of the generated output file. The file
    will be placed in `<path to data dir on host>`.

### HTTP Service Mode
The following command can be used to run the HTTP service container

  	docker run -t -i qa_baseline_http

The command above will start a container that answers questions
each submitted as an HTTP request, for example

  	curl -XPOST --header "Content-Type: application/json" -d '{"char_position":112, "question_text": "At its premiere, the librettist of this opera portrayed a character who asks for a glass of wine with his dying wish", "Incremental_text":"a glass of wine with his dying wish","Is_new_sent":false }' http://localhost/qa

which returns a json response

  	{"guess": "The_Marriage_of_Figaro", "buzz": true}
