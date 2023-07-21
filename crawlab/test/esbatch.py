import uuid

import requests
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
# 连接到Elasticsearch实例
def esBatch(docList:list):
    es = Elasticsearch(['8.217.110.233:9200'])
    #es = Elasticsearch("http://192.168.1.1:9200", http_auth=('username', 'password'), timeout=20)
    index_name = 'aifin_test1'
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name)
    # 定义要插入的文档数据
    # 使用bulk()方法批量插入文档
    actions = [
        {
            '_index': index_name,
            '_source': doc
        }
        for doc in docList
    ]
    bulk(es, actions)

if __name__ == '__main__':
    print(uuid.uuid1())

