#!/usr/bin/env python3

import time
import argparse
import httplib2
import _thread

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from threading import Thread


class HttpRequest(Thread):
    stop = False
    request_depth = 0
    lock = _thread.allocate_lock()

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
            if not self.do_request(self.url) or self.stop:
                break

    def do_request(self, url, depth=0):
        time.sleep(self.delay_between_each_call)

        self.lock.acquire()
        if not self.stop:
            print('Requesting..', url)
        self.lock.release()

        if not self.stop:
            http = httplib2.Http()
            if len(self.username) > 0 and len(self.password) > 0:
                http.add_credentials(self.username, self.password)
            try:
                header, content = http.request(url)
                if self.do_like_a_spider:
                    links = self.get_links(content.decode(), url, self.root_url)
                    for link in links:
                        if depth <= self.request_depth:
                            self.do_request(link, depth + 1)
            except:
                if self.stop_on_error:
                    self.stop = True
                return False

            return True
        else:
            return False

    @staticmethod
    def get_links(html, base_url, root_url):
        result = []
        html_parser = BeautifulSoup(html, 'lxml')
        anchor_tags = html_parser.find_all('a')
        for tag in anchor_tags:
            url = urljoin(base_url, tag.get('href')).split('#')[0]
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
HttpRequest.stop = False
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

input('Done.. Press ENTER to exit...')
