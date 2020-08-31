"""
    Download a file with content requests and threading

    Note:
        must use integer Content-Length, offset in Content-Range, and file seek.

    Logic:
        get Content-Length from request.head(url)
        calculators offsets through Content-Length
        add offset to new headers
        content request each part of the download file with threading

    HTTP Header:
        1. request.head
        {'Date': 'Sun, 18 Nov 2018 15:42:14 GMT', 'Server': 'Apache', 'Last-Modified': 'Fri, 17 Nov 2017 21:04:42 GMT', 'ETag': '"c6c82-55e3415e20e80"', 'Accept-Ranges': 'bytes', 'Content-Length': '814210', 'Keep-Alive': 'timeout=2, max=100', 'Connection': 'Keep-Alive', 'Content-Type': 'application/pdf'}
        2. request.get
        {'Date': 'Sun, 18 Nov 2018 15:44:31 GMT', 'Server': 'Apache', 'Last-Modified': 'Fri, 17 Nov 2017 21:04:42 GMT', 'ETag': '"c6c82-55e3415e20e80"', 'Accept-Ranges': 'bytes', 'Content-Length': '8143', 'Content-Range': 'bytes 56994-65136/814210', 'Keep-Alive': 'timeout=2, max=100', 'Connection': 'Keep-Alive', 'Content-Type': 'application/pdf'}
"""
import threading
import time
import requests

class ContentRequest():
    """HTTP File Threading Download with Request Content """
    def __init__(self, url, threads, path=''):
        """class init"""
        self.url = url
        self.threads = threads
        self.file = path + self.url.split('/')[-1]
        self.resp = {}
        self.reload = ()  # use tuple to avoid duplicate value
        self.content_length = 0

    def get_offset(self):
        """calculate the offset base on the content-length and threading"""
        resp = requests.head(self.url)
        self.content_length = int(resp.headers['Content-Length'])
        offset = int(self.content_length / self.threads)
        for i in range(self.threads):
            if i < self.threads - 1:
                yield (i * offset, (i + 1) * offset)
            else:
                yield (i * offset, '')

    def request_content(self, headers):
        """request content download, the response code should be 206"""
        # try 5 times totally if error happen
        for i in range(1, 6):
            try:
                offset = headers['Range'].split('=')[1].split('-')[0]
                resp = requests.get(self.url, headers=headers)
                if resp.status_code == 206:  # 206 Partial Content
                    self.resp[offset] = resp
                else:
                    print(resp.status_code)
                    self.reload += (headers, )
                return
            except requests.exceptions.RequestException as err:
                print(err.args)
                print('--Error! Retry in {} seconds...'.format(i * 3))
                time.sleep(i * 3)
        print('--Failed to get {} / {} in 5 times retry.'.format(headers, self.file))

    def write_file(self, resp):
        """save to binary file"""
        with open(self.file, 'wb') as opened_file:
            for response in resp:
                # Content-Range: bytes 0-81421/814210
                start = int(response.headers['Content-Range'].split('-')[0].split(' ')[-1])
                opened_file.seek(start)
                opened_file.write(response.content)

    def start(self):
        """stat threading download"""
        start_time = time.time()
        offset_range = self.get_offset()
        # replace the get_headers function with one line use generator
        # {'Content': 'Bytes=0-81421', 'Accept-Encoding': '*'}
        headers = ({'Range': 'Bytes={}-{}'.format(*item), 'Accept-Encoding': '*'} for item in offset_range)
        threads_list = []

        for header in headers:
            thread = threading.Thread(target=self.request_content, args=(header,))
            thread.start()
            threads_list.append(thread)

        for thread in threads_list:
            thread.join()

        if len(self.reload) == 0:
            # for resp in self.resp.values():
            self.write_file(self.resp.values())
            time_used = round(time.time() - start_time, 2)
            file_name = self.file.split('/')[-1]
            speed_mb = round(self.content_length / time_used / 1000000, 2)
            # use round to limit the length after decimal
            print(f'File {file_name} downloaded in {time_used} seconds. (Speed: {speed_mb} MB/s)')
        else:
            print('Error!')
            print(self.reload)


def main():
    """main function"""
    url = 'https://www.python.org/ftp/python/3.8.5/Python-3.8.5.tgz'

    threads = 100
    path = './'

    http_download = ContentRequest(url, threads, path)
    http_download.start()

if __name__ == '__main__':
    main()
