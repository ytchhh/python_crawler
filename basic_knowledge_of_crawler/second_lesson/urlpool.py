#Author: veelion

import pickle
import time
import urllib.parse as urlparse
from urldb import UrlDB

class UrlPool:
    '''URL Pool for crawler to manage URLs
    '''

    def __init__(self, pool_name):
        self.name = pool_name
        self.db = UrlDB(pool_name)

        self.waiting = {}  # {host: set([urls]), } 按host分组，记录等待下载的URL
        self.pending = {}  # {url: pended_time, } 记录已被取出（self.pop()）但还未被更新状态（正在下载）的URL
        self.failure = {}  # {url: times,} 记录失败的URL的次数
        self.failure_threshold = 3
        self.pending_threshold = 10  # pending的最大时间，过期要重新下载
        self.waiting_count = 0  # self.waiting 字典里面的url的个数
        self.max_hosts = ['', 0]  # [host: url_count] 目前pool中url最多的host及其url数量
        self.hub_pool = {}  # {url: last_query_time, }  存放hub url
        self.hub_refresh_span = 0
        self.load_cache()

    def __del__(self):
        self.dump_cache()

    def load_cache(self):
        path = self.name + '.pkl'
        try:
            with open(path, 'rb') as f:
                self.waiting = pickle.load(f)
            cc = [len(v) for k, v in self.waiting.items()]
            print('saved pool loaded! urls:', sum(cc))
        except:
            pass

    def dump_cache(self):
        path = self.name + '.pkl'
        try:
            with open(path, 'wb') as f:
                pickle.dump(self.waiting, f)
            print('self.waiting saved!')
        except:
            pass

    def set_hubs(self, urls, hub_refresh_span):
        self.hub_refresh_span = hub_refresh_span
        self.hub_pool = {}
        for url in urls:
            self.hub_pool[url] = 0

    def set_status(self, url, status_code):
        #先将url从pending中删除，
        if url in self.pending:
            self.pending.pop(url)
        #服务器成功处理url
        if status_code == 200:
           self.db.set_success(url)
            return
        #服务器返回处理错误消息
        if status_code == 404:
            self.db.set_failure(url)
            return
        #如果url已经在失败的字典里面，将失败的次数++，如果次数超过失败的最大次数，将其永久记录为失败，不再尝试。
        if url in self.failure:
            self.failure[url] += 1
            if self.failure[url] > self.failure_threshold:
                self.db.set_failure(url)
                self.failure.pop(url)
            else:
                self.add(url)
        else:
            #未达到最大失败次数，重新入池
            self.failure[url] = 1
            self.add(url)

    def push_to_pool(self, url):
        host = urlparse.urlparse(url).netloc
        if not host or '.' not in host:
            print('try to push_to_pool with bad url:', url, ', len of ur:', len(url))
            return False
        #如果该host已经在waiting字典里面，并且该url也在该host对应的url列表里面
        if host in self.waiting:
            if url in self.waiting[host]:
                return True
            self.waiting[host].add(url)
            #如果该 host的url数量超过最大的host对应的url数量，更新最大的host对应的url
            if len(self.waiting[host]) > self.max_hosts[1]:
                self.max_hosts[1] = len(self.waiting[host])
                self.max_hosts[0] = host
        else:
            self.waiting[host] = set([url])
        self.waiting_count += 1
        return True

    def add(self, url, always=False):
        if always:
            return self.push_to_pool(url)
        #先检查内存中的self.pending是否存在该url，即是否正在下载该url。如果正在下载就不入池
        pended_time = self.pending.get(url, 0)
        if time.time() - pended_time < self.pending_threshold:  #表示正在被下载
            print('being downloading:', url)
            return
        ##该url是否已经在leveldb中存在就表明之前已经成功下载或彻底失败，不再下载了也不入池
        if self.db.has(url):
            return
        ##超时了已经
        if pended_time:
            self.pending.pop(url)
        return self.push_to_pool(url)

    def addmany(self, urls, always=False):
        if isinstance(urls, str):
            print('urls is a str !!!!', urls)
            self.add(urls, always)
        else:
            for url in urls:
                self.add(url, always)

    def pop(self, count, hub_percent=50):
        print('\n\tmax of host:', self.max_hosts)

        # 取出的url有两种类型：hub=1, 普通=0
        url_attr_url = 0
        url_attr_hub = 1
        # 1. 首先取出hub，保证获取hub里面的最新url.
        hubs = {}
        hub_count = count * hub_percent // 100
        #遍历hub_pool，检查每个hub-url距上次被pop的时间间隔是否超过hub页面刷新间隔(self.hub_refresh_span)，来决定hub-url是否应该被pop
        for hub in self.hub_pool:
            span = time.time() - self.hub_pool[hub]
            if span < self.hub_refresh_span:
                continue
            hubs[hub] = url_attr_hub # 1 means hub-url
            self.hub_pool[hub] = time.time()
            if len(hubs) >= hub_count:
                break

        # 2. 再取出普通url
        left_count = count - len(hubs)
        urls = {}
        for host in self.waiting:
            if not self.waiting[host]:
                continue
            url = self.waiting[host].pop()
            urls[url] = url_attr_url
            self.pending[url] = time.time()
            if self.max_hosts[0] == host:
                self.max_hosts[1] -= 1
            if len(urls) >= left_count:
                break
        self.waiting_count -= len(urls)
        print('To pop:%s, hubs: %s, urls: %s, hosts:%s' % (count, len(hubs), len(urls), len(self.waiting)))
        urls.update(hubs)
        return urls

    def size(self,):
        return self.waiting_count

    def empty(self,):
        return self.waiting_count == 0
