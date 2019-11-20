**比较大型的爬虫来说，URL管理的管理是个核心问题，管理不好，就可能重复下载，也可能遗漏下载。这里，我们设计一个URL Pool来管理URL**

URL Pool就是一个生产者消费者模式：

关于生产者消费者模式：[这儿有一篇文章介绍](https://blog.csdn.net/kaiwii/article/details/6758942)
```
graph LR
A[生产者] --> |生产| B[产品池]
B --> |消费| C[消费者]
```
因此，网址池就应该是这个模样
```
graph LR
A[网页解析] --> |新URL| B[网址池]
B --> |取URL| C[爬虫]
C --> |下载| A
```
- 首先网址池应该有以下三个基本功能：
    - ==往池子里面添加URL==
    - ==从池子里面取URL以下载；==
    - ==池子内部要管理URL状态==
- URL的状态应该有以下4种：
    - ==已经下载成功==
    - ==下载多次失败无需再下载==
    - ==正在下载==
    - ==下载失败要再次尝试==
前面两个是永久状态，也就是已经下载成功的不再下载，多次尝试后仍失败的也就不再下载，它们需要永久存储起来，以便爬虫重启后，这种永久状态记录不会消失，已经成功下载的URL不再被重复下载。因此接下来我们需要进行==永久存储==，永久存储的方法有：
    - 直接写入文本文件，但它不利于查找某个URL是否已经存在文本中
    - 直接写入MySQL等关系型数据库，它利用查找，但是速度又比较慢
    - ==使用key-value数据库，查找和速度都符合要求，是不错的选择==
目前实现的URLPOOL选LEVELDB来作为URL状态的永久存储。LevelDB是Google开源的一个key-value数据库，速度非常快，同时自动压缩数据。我们用它先来实现一个UrlDB作为永久存储数据库。[关于LEvelDBde的介绍](https://blog.csdn.net/linuxheik/article/details/52768223)
    - URLDb主要是有三个方法是背使用的：
        - has(url) 查看是否已经存在某url
        - set_success(url) 存储url状态为成功
        - set_failure(url) 存储url状态为失败
    URLDb类的使用不用做过多的介绍了，就上面三个方法，结构也十分清晰。

#### 主要介绍以下URLPool(网址池)的实现
先介绍以下里面的成员
- self.db 是一个UrlDB的示例，用来永久存储url的永久状态。
- self.waiting是一个字典，按照host分组，value是用来存储这个host的所有URL的集合。
- self.pending记录已被取出（self.pop()）但还未被更新状态（正在下载）的URL。key是url，value是它被pop的时间戳。当一个url被pop()时，就是它被下载的开始。
- self.failue 是一个字典，key是url，value是识别的次数，超过failure_threshold就会被永久记录为失败，不再尝试下载。
- 1. hub_pool 是一个用来存储hub页面的字典，key是hub url，value是上次刷新该hub页面的时间.
再介绍以下里面的方法：
-  load_cache() 和 dump_cache() 对网址池进行缓存
    - load_cache() 在 init()中调用，创建pool的时候，尝试去加载上次退出时缓存的URL pool；
    dump_cache() 在 del() 中调用，也就是在网址池销毁前（比如爬虫意外退出），把内存中的URL pool缓存到硬盘。  
- 2. set_hubs() 方法设置hub URL
    - hub网页就是像百度新闻那样的页面，整个页面都是新闻的标题和链接，是我们真正需要的新闻的聚合页面，并且这样的页面会不断更新，把最新的新闻聚合到这样的页面，我们称它们为hub页面，其URL就是hub url。在新闻爬虫中添加大量的这样的url，有助于爬虫及时发现并抓取最新的新闻。该方法就是将这样的hub url列表传给网址池，在爬虫从池中取URL时，根据时间间隔（self.hub_refresh_span）来取hub url。
    - add(), addmany(), push_to_pool() 对网址池进行入池操作
- 3. add(), addmany(), push_to_pool() 对网址池进行入池操作
    - 把url放入网址池时，先检查内存中的self.pending是否存在该url，即是否正在下载该url。如果正在下载就不入池；如果正下载或已经超时，就进行到下一步；
    - 接着检查该url是否已经在leveldb中存在，存在就表明之前已经成功下载或彻底失败，不再下载了也不入池。如果没有则进行到下一步；
    - 最后通过push_to_pool() 把url放入self.pool中。存放的规则是，按照url的host进行分类，相同host的url放到一起，在取出时每个host取一个url，尽量保证每次取出的一批url都是指向不同的服务器的，这样做的目的也是为了尽量减少对抓取目标服务器的请求压力。力争做一个服务器友好的爬虫 
- 4. pop() 对网址池进行出池操作
    - 爬虫通过该方法，从网址池中获取一批url去下载。取出url分两步：
    - 第一步，先从self.hub_pool中获得，方法是遍历hub_pool，检查每个hub-url距上次被pop的时间间隔是否超过hub页面刷新间隔(self.hub_refresh_span)，来决定hub-url是否应该被pop。
    - 第二步，从self.pool中获取。前面push_to_pool中，介绍了pop的原则，就是每次取出的一批url都是指向不同服务器的，有了self.pool的特殊数据结构，安装这个原则获取url就简单了，按host（self.pool的key）遍历self.pool即可。
- 5. set_status() 方法设置网址池中url的状态
    - 其参数status_code 是http响应的状态码。爬虫在下载完URL后进行url状态设置。
    - 首先，把该url成self.pending中删除，已经下载完毕，不再是pending状态；
    - 接着，根据status_code来设置url状态，200和404的直接设置为永久状态；其它status就记录失败次数，并再次入池进行后续下载尝试。
