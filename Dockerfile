FROM ubuntu:20.04

RUN apt-get -q update
RUN apt-get install -y python3-pip

ARG POIFIER_USER=poifier
ARG POIFIER_HOME=/home/poifier

RUN useradd -m -d "${POIFIER_HOME}" -s /bin/bash "${POIFIER_USER}"

COPY poifier-client.py "${POIFIER_HOME}/poifier-client.py"

RUN chmod +x "${POIFIER_HOME}/poifier-client.py"
RUN chown $POIFIER_USER:$POIFIER_USER "${POIFIER_HOME}/poifier-client.py"

USER $POIFIER_USER
WORKDIR $POIFIER_HOME

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3", "poifier-client.py" ]
