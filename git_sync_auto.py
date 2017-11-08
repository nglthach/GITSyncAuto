#!/usr/bin/env python3

from argparse import ArgumentParser

import getpass
import pexpect
import signal
import time
import re
import os


def read_output(pexpect):
    temp = os.read(pexpect.child_fd, 100000)
    if len(temp) > 0:
        result = temp.decode().strip('\r\n')
        if result is None and pexpect.closed:
            return pexpect.read()

        return result
    return ''


def print_result(out, p):
    print(out)
    # Wait for the process finished
    time.sleep(3)
    if p.isalive():
        p.kill(signal.SIGKILL)


# Parse the arguments
arg_parser = ArgumentParser()
arg_parser.add_argument('--delay', type=int)
args = arg_parser.parse_args()
# Get git credentials
username = input('GIT Username: ')
password = getpass.getpass('GIT Password: ')

while True:
    print('Synchronizing...')
    # Run git command
    p = pexpect.spawnu('git pull')
    # Interact with git
    while True:
        # Wait for the output
        time.sleep(1)
        # Read the output
        out = read_output(p)
        # Check if there is any error
        if re.search(r'fatal', out, re.I):
            print_result(out, p)
            break
        # Check if git is waiting for username
        elif re.search(r'username', out, re.I):
            print('Sending username...')
            p.sendline(username)
        # Check if git is waiting for password
        elif re.search(r'password', out, re.I):
            print('Sending password...')
            p.sendline(password)
        # Error or git output
        else:
            print_result(out, p)
            break

    # Sleep awhile before next run
    time.sleep(args.delay if args.delay else 5)
