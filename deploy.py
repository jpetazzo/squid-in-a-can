#!/usr/bin/env python

# Copyright (c) 2014, Tully Foote

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.



import os
import subprocess
import socket
import sys
import time

build_cmd = 'docker build -t local-squid-in-a-can .'
squid_cmd = 'docker run --net host local-squid-in-a-can'
redirect_cmd = 'iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to 3129 -w'
remove_redirect_cmd = redirect_cmd.replace(' -A ', ' -D ')

LOCAL_PORT=3128

def is_port_open(port_num):
    """ Detect if a port is open on localhost"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return sock.connect_ex(('127.0.0.1',port_num)) == 0


class RedirectContext:
    """ A context to make sure that the iptables rules are removed
    after they are inserted."""
    def __enter__(self):
        print("Enabling IPtables forwarding: '%s'" % redirect_cmd)
        subprocess.check_call(redirect_cmd.split())
        return self

    def __exit__(self, type, value, traceback):
        print("Disabling IPtables forwarding: '%s'" % remove_redirect_cmd)
        subprocess.check_call(remove_redirect_cmd.split())



def main():
    if os.geteuid() != 0:
        print("This must be run as root, aborting")
        return -1
    # build the docker instance as a subprocess
    subprocess.check_call(build_cmd, shell=True)

    # Start the docker instance as a subprocess
    squid_in_a_can = subprocess.Popen(squid_cmd, shell=True)

    # While the process is running wait for squid to be running
    while squid_in_a_can.poll() is None and not is_port_open(LOCAL_PORT):
        print("Waiting for port %s to open" % LOCAL_PORT)
        time.sleep(1)

    if is_port_open(LOCAL_PORT):
        print("Port %s detected open setting up IPTables redirection" % LOCAL_PORT)
        with RedirectContext():
            # Wait for the docker instance to end or a ctrl-c
            try:
                while squid_in_a_can.poll() is None and is_port_open(LOCAL_PORT):
                    time.sleep(1)
            except KeyboardInterrupt as ex:
                # Catch Ctrl-C and pass it into the docker instance
                print("CTRL-C caught, shutting down.")
                squid_in_a_can.terminate()

    else:
        print("Port %s never opened, docker instance must have terminated prematurely." % LOCAL_PORT)

    squid_in_a_can.poll()
    print("Docker process exited with return code %s" % squid_in_a_can.returncode)
    return squid_in_a_can.returncode

if __name__ == '__main__':
    sys.exit(main())
