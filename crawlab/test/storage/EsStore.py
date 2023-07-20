###################### es操作 ###############################################
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
# 连接到Elasticsearch实例
def storeData(docList:list,index_name:str='aifin',path:str='172.28.84.188:9200'):
    es = Elasticsearch([path])
    #es = Elasticsearch("http://192.168.1.1:9200", http_auth=('username', 'password'), timeout=20)
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
    count = 0
    esObj = None
    while True and count < 3:
        try:
            esObj = bulk(es, actions)
            break
        except Exception as e:
            print(f"error,写入ES库异常,{e}")
            count += 1
    if not esObj:
        raise Exception("写入ES库异常")
    print(f"写入ES【{index_name}】库over")
