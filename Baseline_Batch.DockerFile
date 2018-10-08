# Start with an anaconda (python 3.5) image
FROM continuumio/anaconda3:5.2.0

# Source the python environment
CMD [ "source /opt/conda/bin/activate" ]

# installing modules 
RUN pip install boto3

# Copy scripts, and trained model

COPY qa_batch.py /app/
COPY tfidf_model /app/tfidf_model/
COPY qanta /app/qanta/
COPY qanta-defaults.yaml /app/

# Install requirements
WORKDIR /app/

# Start command

ENTRYPOINT [ "python", "qa_batch.py" ]


