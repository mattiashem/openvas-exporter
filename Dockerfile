FROM ubuntu:latest


#Install logstash
RUN apt-get update && apt-get install wget gnupg2 gnupg1 default-jre -y
RUN wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -
RUN apt-get install apt-transport-https -y
RUN echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-7.x.list
RUN apt-get update &&  apt-get install logstash -y


#Install python deps
RUN apt-get update && apt-get install gettext-base python3 python3-pip telnet curl vim -y
RUN pip3 install gvm-tools untangle
RUN pip3 install --user python-gvm


#Setup User
RUN useradd gvm
RUN mkdir /home/gvm
COPY code/ /home/gvm
RUN chown gvm:gvm -R /home/gvm

#Setup defult settings
ENV USERNAME=admin
ENV PASSWORD=admin
ENV GSAD_HOST=gvmd
ENV DATA=data




#Setup run script
COPY run.sh /run.sh
RUN chmod +x /run.sh
USER gvm
WORKDIR /home/gvm/
CMD ./run.sh