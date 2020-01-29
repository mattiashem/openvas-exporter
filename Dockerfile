FROM ubuntu:latest


RUN apt-get update && apt-get install python3 python3-pip telnet curl vim -y
RUN pip3 install gvm-tools untangle


RUN useradd gvm
RUN mkdir /home/gvm
COPY gmp.conf /home/gvm


RUN chmod 777 /home/gvm

RUN pip3 install --user python-gvm
USER gvm
WORKDIR /home/gvm/