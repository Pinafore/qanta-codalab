# Installation

You will only need to have [docker](https://docker.com) and `docker-compose`
installed to run this reference system. There are no other requirements since
everything inside of the container.

# Reference System

We provide an example [docker](http://docker.com) container for answering Quiz
Bowl questions. This should both provide an example of how the codalab server
interacts with the container as well as a simple yet surprisingly effective
baseline. The simple system consists of a TF-IDF guesser and a threshold-based
buzzer.  The input unit to the system is a question (sequence of words) and the
system outputs an answer guess (a Wikipedia entity) and a binary decision
whether to buzz or not.

We provide two methods for interacting with the docker container—**Batch
container** and **HTTP service container**.  In the batch mode, the container
is run for a given input file that consists of multiple questions, one question
per line.  The container produces an output file that consists of answers to
each of the given questions. The HTTP service container starts a background
service that processes POST requests (submitted for example using a Curl
command), where each request is an individual question. The HTTP service
container is more suitable for the incremental question answering setup (e.g.,
when questions are provided word-by-word).

# Running

There are four commands you can run with the provided files in this repository:

```
docker-compose run qb ./cli download
docker-compose run qb ./cli train
docker-compose run qb ./cli web
docker-compose run qb ./cli batch input_file output_file
```

Under the hood `docker-compose` references the `docker-compose.yml` file. The
first argument `run` instructs the program to run the service named `qb` from
the configuration with the arguments `./cli stuff_goes_here`. `docker-compose`
will also automatically take care of building the container which contains all
the model's dependencies. The effect of each command is described below:

1. `download` will download the quiz bowl training dataset to `data/`
2. `train` will use the downloaded data to train a tfidf based guesser and
   static threshold buzzer saved to `models/`
3. `web` will start a web server that the codalab server will interact with
4. `batch` is a convenience for computing guess/buzz outcomes in batch.

Running these commands downloads the data and trains a model

```bash
docker-compose run qb ./cli download
docker-compose run qb ./cli train
```

This command will start the web server. Issuing `ctrl-c` will stop the server.

```bash
docker-compose up
```

After that is running you can run this command (requires
[httpie](https://httpie.org/)) to verify things work correctly:

```bash
$ http --form POST http://0.0.0.0:4861/api/1.0/quizbowl/act question_text='Name the the inventor of general relativity and the photoelectric effect'
HTTP/1.0 200 OK
Content-Length: 41
Content-Type: application/json
Date: Wed, 10 Oct 2018 01:12:27 GMT
Server: Werkzeug/0.14.1 Python/3.7.0

{
    "buzz": false,
    "guess": "Albert_Einstein"
}
```

The codalab evaluation servers will use similar commands to run scoring so it
is important that your system responds correctly to this specific HTTP
endpoint.

# Input/Output Formats
In addition to the `question_text` field shown in the `httpie` sample request,
we also provide the following fields which you may find useful.

 * `char_position` Character position of provided question text
 * `question_text` Question text up to `char_position`
 * `incremental_text` Incremental text from last position to current position
 * `tossup_number` question number
 * `sent_number` The current sentence number. (starting from 0 for the tokens
   in the first sentence of the questions)


## Example Input

   	{"char_position":112, "question_text": "At its premiere, the librettist of this opera portrayed a character who asks for a glass of wine with his dying wish", "incremental_text":"a glass of wine with his dying wish", "tossup_number": 1, "sent_number": 0}

The output answer to each question is also a json object of two fields
 * `guess` Guessed Wikipedia answer entity
 * `buzz` true/false whether to buzz given the seen question text so far or not

## Example Output

  	{"guess": "The_Marriage_of_Figaro", "buzz": true}

# Dockerhub Maintainer Notes

The default docker-compose file references the published image for quizbowl at
https://hub.docker.com/r/entilzha/quizbowl/

To push new images requires the correct permissions and running the following
commands in sequence:

```bash
docker-compose -f docker-compose.dev.yml build
docker tag qanta-codalab_qb:latest entilzha/quizbowl
docker push entilzha/quizbowl
```

