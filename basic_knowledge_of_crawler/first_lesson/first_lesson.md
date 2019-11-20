#### Web基础概念
- 学习爬虫必须弄懂的问题：
    - 从输入网址到看到网页，发生的过程。
    - URL的概念,统一资源定位符。
- 工具ipython的使用
    - 自动补全，运行系统命令，查看模块函数功能。
- requests用法，
    - r.cookies，
    - r.text(网页源代码)，
    - r.content(网页二进制数据)，
    - r.encoding(获取编码)，
        - 使用chaerdet.detect(r.content)来检测编码。 gb2312 < gbk < gb18030。chaerdet.detect方法有的时候不太准确。因此用ccharset模块，cchardet.detect()方法。
-  HTTP请求主要方法：
    - GET和POST
#### 爬虫的一般步骤
- 浏览器打开要抓取的网站
    - 推荐chrome浏览器
    - f12调出开发者工具
- 查看源代码，是否包含想要的数据
    - 包含，则通过requests库抓取网页，提取数据。 
- 检查ajax请求
    - 寻找需要的数据 
#### 爬虫的基本操作
-  抓取 将html存储(压缩)
    - 网页
    - ajax
-   提取
    - re 正则表达式
    - lxml (Beautiful Soup)
    -xpath()
-   存储至数据库
#### HTTP请求库
-   urllib.request
-   requests( 同步IO请求) aiohttp(异步IO请求)
    - r.text
    - r.content
    - r.json
- ccharset编码(C++实现)
- selenium 自动化测试工具   
    - webdriver.chrome()
    - chrome headless 

#### 爬虫进阶
- 用chrome断点调试JavaScript
- 用Charles，Fiddle抓包分析

#### 如何发现ajax加载URL
- Chrome浏览器f12调出开发者工具
    - Network
        - Type:xhr
        - Filter:XHR(Doc)
    -  返回结果
        - json,xml,html
    - 例子
    https://translate.google.com

#### 瀑布流网页的抓取
- 表现是瀑布流，实现是ajax

#### js解密
-   打开网页加载的js 
-   晦涩难懂，pretty格式但变量，函数名难懂
-   找到js加密/解密算法的代码
-   Charles抓包解析
    - 例子:新浪微博登陆加密
-   Chrome调试JavaScript

#### 对付JavaScript的万能钥匙
- Python Selenium模块
    - Chrome有界面
    - Chrome Headless
- Chrome的运行效率
    - 没有requests等库快，但开发速度快
        - 不用费劲理解JavaScript代码
        - 不用使用Python重写JavaScript
    - 针对单一复杂网站，建议Chrome
        - 很难绕开该网站的IP，账号限流。
    - 很多普通网站，使用requests
        - 这些网站几乎没有限制

#### 异步并发爬虫

```
graph TD
A((网址池)) -->|one| B[下载器]
A((网址池)) -->|two| C[下载器]
A((网址池)) -->|Three| D[下载器]
B --> E{HTML数据库}
C --> E{HTML数据库}
D --> E{HTML数据库}

E --> G((提取器))
G --> H{目标数据库}
```

#### 分布式爬虫

