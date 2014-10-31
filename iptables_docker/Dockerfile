FROM debian:jessie
RUN apt-get -q update
RUN apt-get -qy install iptables
RUN apt-get -qy install python
ADD deploy.py /tmp/deploy.py
CMD /tmp/deploy.py
