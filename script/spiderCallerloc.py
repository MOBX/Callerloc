#!/usr/bin/env python
# encoding: utf-8

"""
@version: 1.0
@author: luckscript
@contact: luckscript@gmail.com
@site: http://www.msun.com
@file: spiderCallerloc.py
@desc: 大陆手机号码归属地爬虫
@time: 17/3/15 10:33
"""

import Queue
import codecs
import json
import threading
import time
import traceback
from collections import OrderedDict

import requests
from bs4 import BeautifulSoup

macs = ["130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
        "145", "146", "147", "148", "149",
        "150", "151", "152", "153", "154", "155", "156", "157", "158", "159",
        "166", "167",
        "170", "171", "172", "173", "174", "175", "176", "177", "178", "179",
        "180", "181", "182", "183", "184", "185", "186", "187", "188", "189",
        "191", "198", "199",
        ]

orig_file = codecs.open("orig_callerloc.json", "w", "utf-8")  # 原始文件
error_file = codecs.open("callerloc_error_mobile", "w", "utf-8")  # 爬取失败文件
res_file = codecs.open("CallerlocChina.json", "w", "utf-8")  # 结果json文件
res_txt_file = codecs.open("CallerlocChina.txt", "w", "utf-8")  # 结果txt文件

mobile_url = 'http://www.ip138.com:8080/search.asp?action=mobile&mobile='

queue = Queue.Queue()


class ThreadUrl(threading.Thread):
    """Threaded Url Grab"""

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    @staticmethod
    def parser(line):
        try:
            obj = json.loads(line)
            if u'未知' in obj['city']:
                print line
                return
            list = obj['city'].split(u'\xa0', 1)
            if u'' in list:
                province = list[0]
                city = list[0]
            else:
                province = list[0]
                city = list[1]
            cityCode = obj['cityCode']
            zipCode = obj['zipCode'].split(' ')[0]
            mobile = obj['mobile'].split(' ')[0][:7]
            operator = obj['operator']
            res_file.write(
                '{ "_id" : "' + mobile + '", "province" : "' + province + '", "city" : "' + city + '", "areacode" : "' + cityCode + '", "zip" : "' + zipCode + '", "company" : "' + operator + '" }' + '\n')
            res_txt_file.write(mobile + ',' + operator + ',' + province + ',' + city + '\n')
        except:
            traceback.print_exc()
            pass

    @staticmethod
    def spider(mobile):
        try:
            html_doc = requests.get(mobile_url + mobile)
            soup = BeautifulSoup(html_doc.content, 'lxml')
            mark = soup.find_all('td', class_="tdc2")
            data = dict(mobile=mark[0].get_text(),
                        city=mark[1].get_text(),
                        operator=mark[2].get_text(),
                        cityCode=mark[3].get_text(),
                        zipCode=mark[4].get_text(),
                        )
            return data
        except:
            error_file.write(mobile)
            traceback.print_exc()
            pass

    def run(self):
        while True:
            # grabs host from queue
            prefix = self.queue.get()

            # do jobs
            for i in range(0001, 9999):
                num = prefix + "{:0>4d}".format(i)
                mobile = num + '8227'
                try:
                    data = self.spider(mobile)
                    sort_data = OrderedDict(sorted(data.items(), key=lambda x: x[1]))
                    json_data = json.dumps(sort_data, ensure_ascii=False)
                    orig_file.write(json_data + '\n')
                    self.parser(json_data)
                    time.sleep(1)
                except:
                    error_file.write(mobile)
                    traceback.print_exc()
                    continue

            # signals to queue job is done
            self.queue.task_done()


start = time.time()


def main():
    # spawn a pool of threads, and pass them queue instance
    for i in range(5):
        t = ThreadUrl(queue)
        t.setDaemon(True)
        t.start()

    # populate queue with data
    for prefix in macs:
        queue.put(prefix)

    # wait on the queue until everything has been processed
    queue.join()


main()
print "Elapsed Time: %s" % (time.time() - start)
orig_file.close()
error_file.close()
res_file.close()
res_txt_file.close()
