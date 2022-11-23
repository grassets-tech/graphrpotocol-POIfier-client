FROM python:3.9.15-alpine3.16

RUN apk --no-cache add gcc musl-dev

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip3 install -r requirements.txt

COPY . .

ENTRYPOINT [ "python3", "./poifier-client.py" ]
