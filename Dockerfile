FROM debian:jessie
RUN apt-get -q update
RUN apt-get -qy install squid3
RUN apt-get -qy install iptables
RUN apt-get -qy install python
RUN echo "http_port 3129 intercept" >> /etc/squid3/squid.conf
RUN echo "maximum_object_size 1024 MB" >> /etc/squid3/squid.conf
RUN echo "cache_dir ufs /var/cache/squid3 5000 16 256" >> /etc/squid3/squid.conf
RUN sed -i "s/^#acl localnet/acl localnet/" /etc/squid3/squid.conf
RUN sed -i "s/^#http_access allow localnet/http_access allow localnet/" /etc/squid3/squid.conf
RUN mkdir -p /var/cache/squid3
RUN chown -R proxy:proxy /var/cache/squid3
ADD deploy.py /tmp/deploy.py
CMD /tmp/deploy.py
