#!/usr/bin/env python3

import getpass
import pexpect
import time

username = input('GIT Username: ')
password = getpass.getpass('GIT Password: ')

while True:
    print('Synchronizing...')
    # Run git command
    p = pexpect.spawnu('git pull')
    # Send Username (if any)
    if len(username) > 0:
        p.expect(r'Username.*')
        p.sendline(username)
    # Send Password (if any)
    if len(password) > 0:
        p.expect(r'Password.*')
        p.sendline(password)
    # Print result
    print(p.read().strip('\r\n'))
    # Wait for 1s
    time.sleep(1)
