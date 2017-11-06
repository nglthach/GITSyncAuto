#!/usr/bin/env python3

import sys
import time
import curses
import argparse
import httplib2
import _thread
import colorama

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from threading import Thread
from colorama import Fore, Back, Style


class HttpRequest(Thread):
    stop = False
    request_depth = 0
    lock = _thread.allocate_lock()
    requested_count = 0
    error_count = 0

    def __init__(self, url, max_request, do_like_a_spider, stop_on_error, delay_between_each_call, username, password):
        self.url = url
        self.max_request = max_request
        self.do_like_a_spider = do_like_a_spider
        self.stop_on_error = stop_on_error
        self.delay_between_each_call = delay_between_each_call
        self.username = username
        self.password = password
        # Create root_url
        parse_result = urlparse(url)
        self.root_url = parse_result.scheme + '://' + parse_result.netloc
        # Call super method
        super(HttpRequest, self).__init__()

    def run(self):
        for i in range(self.max_request):
            if (not self.do_request(self.url) and self.stop_on_error) or HttpRequest.stop:
                break

    def do_request(self, url, depth=0):
        time.sleep(self.delay_between_each_call)

        if not HttpRequest.stop:
            self.print_status(url)
            http = httplib2.Http()
            if len(self.username) > 0 and len(self.password) > 0:
                http.add_credentials(self.username, self.password)
            try:
                header, content = http.request(url)
                if self.do_like_a_spider and depth <= self.request_depth:
                    links = self.get_links(content.decode(), url, self.root_url)
                    for link in links:
                        self.do_request(link, depth + 1)
            except:
                self.inc_error()
                if self.stop_on_error:
                    HttpRequest.stop = True
                return False

            return True
        else:
            return False

    @staticmethod
    def print_status(url):
        HttpRequest.lock.acquire()
        HttpRequest.requested_count = HttpRequest.requested_count + 1
        print_with_color(1, 0, Fore.GREEN, 'Requested: ' + str(HttpRequest.requested_count).rjust(10) + '    -    ' + Fore.RED + 'Error: ' + str(HttpRequest.error_count).rjust(10))
        print_with_color((HttpRequest.requested_count - 1) % 10 + 2, 0, Fore.WHITE, 'Requesting..' + url, end='\n\r')
        HttpRequest.lock.release()

    @staticmethod
    def inc_error():
        HttpRequest.lock.acquire()
        HttpRequest.error_count = HttpRequest.error_count + 1
        HttpRequest.lock.release()

    @staticmethod
    def get_links(html, base_url, root_url):
        result = []
        html_parser = BeautifulSoup(html, 'lxml')
        anchor_tags = html_parser.find_all('a')
        for tag in anchor_tags:
            url = urljoin(base_url, tag.get('href')).split('#')[0]
            url.rstrip(r'/')
            try:
                result.index(url)
            except ValueError:
                try:
                    if url.index(root_url) == 0:
                        result.append(url)
                except:
                    pass

        result.sort()
        return result


def pos_escape(y, x):
    return '\x1b[%d;%dH' % (y, x)


def clear_screen():
    print('\033[2J')


def print_with_color(row, col, color, text, end=''):
    print(pos_escape(row, col) + color + text, Style.RESET_ALL, end=end)
    sys.stdout.flush()


# Init screen handler
stdscr = curses.initscr()
stdscr.refresh()
colorama.init()
# Parse the arguments
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('--num_of_thread', help='Num of thread', type=int)
arg_parser.add_argument('--max_request_per_thread', help='Max request per thread', type=int)
arg_parser.add_argument('--do_like_a_spider', help='Do like a spider', type=str)
arg_parser.add_argument('--stop_on_error', help='Stop on error', type=str)
arg_parser.add_argument('--delay_between_each_call', help='Delay between each call', type=int)
arg_parser.add_argument('--username', help='Username for Basic-Authentication', type=str)
arg_parser.add_argument('--password', help='Password for Basic-Authentication', type=str)
arg_parser.add_argument('--url', help='Url', type=str, required=True)
args = arg_parser.parse_args()
# Prepare params
num_of_thread = args.num_of_thread if args.num_of_thread else 10
max_request_per_thread = args.max_request_per_thread if args.max_request_per_thread else 100
do_like_a_spider = args.do_like_a_spider == 'true' if args.do_like_a_spider else True
stop_on_error = args.stop_on_error == 'true' if args.stop_on_error else True
delay_between_each_call = args.delay_between_each_call if args.delay_between_each_call else 0
username = args.username if args.username else ''
password = args.password if args.password else ''
url = args.url
# Run..
requests = []
for i in range(num_of_thread):
    request = HttpRequest(url, max_request_per_thread, do_like_a_spider, stop_on_error, delay_between_each_call, username, password)
    requests.append(request)
    request.start()

try:
    # Wait for all requests finished
    for request in requests:
        request.join()
except KeyboardInterrupt:
    HttpRequest.stop = True

if HttpRequest.requested_count >= 9:
    print_with_color(12, 0, Fore.YELLOW, 'Done..Press ENTER to exit...')
else:
    print_with_color((HttpRequest.requested_count % 10) + 3, 0, Fore.YELLOW, 'Done..Press ENTER to exit...')

stdscr.getkey()
curses.endwin()
