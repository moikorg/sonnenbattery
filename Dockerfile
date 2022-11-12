FROM python:3.10-alpine

RUN apk update && apk upgrade && apk add bash 
RUN pip install --upgrade pip


RUN rm -rf /var/cache/apk/*

RUN mkdir /code
WORKDIR /code
ADD code/requirements.txt /code/
RUN pip3 install -r requirements.txt
ADD code/* /code/
ENTRYPOINT ["python3"]
CMD ["sonnenbattery.py"]
#CMD ["sonnenbattery.py", "-v"]
