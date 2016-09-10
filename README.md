# Transparent Squid in a container

This is a trivial Dockerfile to build a proxy container.
It will use the famous Squid proxy, configured to work in transparent mode.


## Why?

If you build a lot of containers, and have a not-so-fast internet link,
you might be spending a lot of time waiting for packages to download.
It would be nice if all those downloads could be automatically cached,
without tweaking your Dockerfiles, right?

Or, maybe your corporate network forbids direct outside access, and require
you to use a proxy. Then you can edit this recipe so that it cascades to the
corporate proxy. Your containers will use the transparent proxy, which itself
will pass along to the corporate proxy.


## How?

You can use the squid proxy directly via docker and iptables rules, there is
also a `docker-compose.yml` for convenience to use `docker-compose up` command to launch the system. For more
information on tuning parameters see below.

### Using Docker and iptables directly.

You can manually run these commands

```bash
docker run --net host -d jpetazzo/squid-in-a-can
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to 3129 -w
```

After you stop you will need to cleanup the iptables rules:
```bash
iptables -t nat -D PREROUTING -p tcp --dport 80 -j REDIRECT --to 3129 -w
```


### Using Compose

There is a `docker-compose.yml` file to enable launching via [docker compose](https://docs.docker.com/compose/) and a separate container
which will setup the iptables rules for you. To use this you will need a
local checkout of this repo and have `docker` and `compose` installed.

> Run the following command in the same directory as the `docker-compose.yml` file:

```bash
docker-compose up
```

### Result

That's it. Now all HTTP requests going through your Docker host will be
transparently routed through the proxy running in the container.

If you your tproxy instance goes down hard without cleaning up use the following command:
```
iptables -t nat -D PREROUTING -p tcp --dport 80 -j REDIRECT --to 3129 -w
```


Note: it will only affect HTTP traffic on port 80.

Note: traffic originating from the host will not be affected, because
the `PREROUTING` chain is not traversed by packets originating from the
host.

Note: if your Docker host is also a router for other things (e.g. if it
runs various virtual machines, or is a VPN server, etc), those things
will also see their HTTP traffic routed through the proxy. They have to
use internal IP addresses, though.

Note: if you plan to run this on EC2 (or any kind of infrastructure
where the machine has an internal IP address), you should probably
tweak the ACLs, or make sure that outside machines cannot access ports
3128 and 3129 on your host.

Note: It will be available to as a proxy on port 3128 on your local machine
if you would like to setup local proxies yourself.


## What?

The `jpetazzo/squid-in-a-can` container runs a really basic Squid3 proxy.
Rather than writing my own configuration file, I patch the default Debian
configuration. The main thing is to enable `intercept` on another port
(here, 3129). To update the iptables for the intercept the command needs
the --privileged flag.

Then, this container should be started using *the network namespace of the
host* (that's what the `--net host` option is for).
Another strategy would be to start the container with its own namespace.
Then, the HTTP traffic can be directed to it with a `DNAT` rule.
The problem with this approach, is that Squid will "see" the traffic as
being directed to its own IP address, instead of the destination HTTP
server IP address; and since Squid 3.3, it refuses to honor such requests.

(The reasoning is, that it would then have to trust the HTTP `Host:`
header to know where to send the request. You can check [CVE-2009-0801]
for details.)


## Tuning

The docker image can be tuned using environment variables.


### MAX_CACHE_OBJECT

Squid has a maximum object cache size. Often when caching debian packages vs
standard web content it is valuable to increase this size. Use the
`-e MAX_CACHE_OBJECT=1024` to set the max object size (in MB)


### DISK_CACHE_SIZE

The squid disk cache size can be tuned. use
`-e DISK_CACHE_SIZE=5000` to set the disk cache size (in MB)


### SQUID_DIRECTIVES_ONLY

The contents of squid.conf will only be what's defined in SQUID_DIRECTIVES
giving the user full control of squid.


### SQUID_DIRECTIVES

This will append any contents of the environment variable to squid.conf.
It is expected that you will use multi-line block quote for the contents.

Here is an example:

```bash
docker run -d \
    -e SQUID_DIRECTIVES="
    # hi ho hi ho
    # we're doing block I/O
    # hi ho hi ho
    " jpetazzo/squid-in-a-can
```


### Persistent Cache

Being docker when the instance exits the cached content immediately goes away
when the instance stops. To avoid this you can use a mounted volume. The cache
location is `/var/cache/squid3` so if you mount that as a volume you can get
persistent caching. Use `-v /home/user/persistent_squid_cache:/var/cache/squid3`
in your command line to enable persistent caching.

If you do that, make sure that the `persistent_squid_cache` directory is
writable by the right user. As I write these lines, the squid process
runs as user and group `proxy`, and their UID and GID both are 13; so
make sure that the directory is writable by UID 13, or by GID 13,
or (if you really can't make otherwise) world-writable (but please don't).

Note that if you're using Docker Mac, all volume I/O is handled by the
Docker Mac application, which runs as an ordinary process; so you won't
have to deal with permissions as long as you have read/write access to
a volume.


## Notes

Ideas for improvement:

- easy chaining to an upstream proxy

### HTTPS support

It has been asked if this could support HTTPS. HTTPS is designed to prevent
man-in-the middle attacks, and a transparent proxy is effectively a MITM.
If you want to use squid for HTTPS proxying transparently you need to setup a
private CA certificate and push it to all your users so they trust the proxy.
An example of how to set this up can be found [here](http://roberts.bplaced.net/index.php/linux-guides/centos-6-guides/proxy-server/squid-transparent-proxy-http-https).

Without a CA certificate configured, the default behavior is to tunnel HTTPS
traffic using the `CONNECT` method. Squid makes the request on behalf of the
client but cannot decrypt or cache the requests or responses.


[CVE-2009-0801]: http://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2009-0801
