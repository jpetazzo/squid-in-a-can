FROM debian:jessie
RUN apt-get -q update && apt-get -qy install iptables python
ADD deploy.py /tmp/deploy.py
CMD /tmp/deploy.py
