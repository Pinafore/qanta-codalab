# Start with an anaconda (python 3.6) image
FROM continuumio/anaconda3:5.3.0

COPY environment.yaml /environment.yaml
RUN conda env create -f environment.yml

# Copy scripts, and trained model

COPY qa_server.py /app/
COPY init.sh /app/
COPY start_server.sh /app/
COPY tfidf_model /app/tfidf_model/
COPY qanta /app/qanta/
COPY qanta-defaults.yaml /app/

# Install requirements
WORKDIR /app/
RUN sh start_server.sh &

# Expose port (based on Balmer series emission line, for science!)
EXPOSE 4861

# Start Service

CMD ./init.sh
