import requests
from bs4 import BeautifulSoup
from ezpymysql import Connection

db = Connection(
    'localhost',
    'sina',
    'root',
    '8018341286'
)
url = 'https://www.sina.com.cn/'
res = requests.get(url)
res.encoding = 'utf-8'

soup = BeautifulSoup(res.text, 'html.parser')

for news in soup.select('.uni-blk-b'):
    a2 = news.select('a')
    for a3 in a2:
     if len(a3) > 0:
        title = a3.text
        href = a3['href']
        sql = 'insert into t_news(title, href) values(%s, %s)'
        last_id = db.execute(sql, title, href)

soup = BeautifulSoup(res.text, 'html.parser')
for news in soup.select('.uni-blk-t clearfix'):
    a2 = news.select('a')
    for a3 in a2:
     if len(a3) > 0:
        title = a3.text
        href = a3['href']
        sql = 'insert into t_news(title, href) values(%s, %s)'
        last_id = db.execute(sql, title, href)

soup = BeautifulSoup(res.text, 'html.parser')
for news in soup.select('.uni-blk-bt'):
    a2 = news.select('a')
    for a3 in a2:
     if len(a3) > 0:
        title = a3.text
        href = a3['href']
        sql = 'insert into t_news(title, href) values(%s, %s)'
        last_id = db.execute(sql, title, href)

