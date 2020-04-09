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

prepare_cache_cmd = "chown -R proxy:proxy /var/cache/squid"
build_cmd = "squid -Nz"
squid_cmd = "squid -N"


def main():
    if os.geteuid() != 0:
        print("This must be run as root, aborting")
        return -1

    # clean up any stale pid files
    if os.path.exists("/run/squid.pid"):
        os.remove("/run/squid.pid")

    max_object_size = os.getenv("MAXIMUM_CACHE_OBJECT", '1024')
    disk_cache_size = os.getenv("DISK_CACHE_SIZE", '5000')
    squid_directives_only = os.getenv("SQUID_DIRECTIVES_ONLY", False)
    arbitrary_squid_directives = os.getenv("SQUID_DIRECTIVES", None)

    squid_conf_entries = []
    squid_conf_entries.append('http_port 3129 intercept')
    squid_conf_entries.append('maximum_object_size %s MB' % max_object_size)
    squid_conf_entries.append('cache_dir ufs /var/cache/squid %s 16 256' %
                              disk_cache_size)

    with open("/etc/squid/squid.conf", 'w') as conf_fh:

        if not squid_directives_only:
            with open("/etc/squid/squid.conf.in", "r") as preconf:
                conf_fh.write(preconf.read())
            for conf in squid_conf_entries:
                print("Appending to squid.conf: [%s]" % conf)
                conf_fh.write(conf + '\n')

        if arbitrary_squid_directives:
            print("Appending squid directives to squid.conf")
            print(arbitrary_squid_directives)
            conf_fh.write(arbitrary_squid_directives)

    # Setup squid directories
    # Reassert permissions in case of mounting from outside
    subprocess.check_call(prepare_cache_cmd, shell=True)
    subprocess.check_call(build_cmd, shell=True)

    # Start the squid instance as a subprocess
    squid_in_a_can = subprocess.Popen(squid_cmd, shell=True)

    # While the process is running wait for squid to be running
    print("Waiting for squid to finish")
    while squid_in_a_can.poll() is None:
        time.sleep(1)

    print("Squid process exited with return code %s" %
          squid_in_a_can.returncode)
    return squid_in_a_can.returncode

if __name__ == '__main__':
    sys.exit(main())
