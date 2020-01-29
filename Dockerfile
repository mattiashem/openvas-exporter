FROM ubuntu:latest


RUN apt-get update && apt-get install gettext-base python3 python3-pip telnet curl vim -y
RUN pip3 install gvm-tools untangle


RUN useradd gvm
RUN mkdir /home/gvm
COPY code/ /home/gvm


RUN chmod 777 /home/gvm


ENV USERNAME=admin
ENV PASSWORD=admin
ENV GSAD_HOST=gvmd
ENV DATA=data


RUN pip3 install --user python-gvm
USER gvm
WORKDIR /home/gvm/