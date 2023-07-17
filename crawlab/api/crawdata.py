# 获取单只股票的数据
import datetime
import json
import sys

import requests
from bs4 import BeautifulSoup


marketMap = {
    32: "深圳证券交易所",
    16: "上海证券交易所",
}

stockMap = {
    "002594": "比亚迪",
    "600887": "伊利股份",
    "300750": "宁德时代",
    "002518": "科士达",
    "600225": "卓朗科技",
    "600977": "中国电影",
    "603259": "药明康德",
    "000063": "中兴通讯",
    "600737": "中粮糖业",
    "300887":"谱尼测试",
}


def buildMarketdata(stock: str, market: int):
    page = 0
    total = 0
    print(f"========开始获取【{stock}】在【{marketMap[market]}】的数据")
    while True:
        print(f"开始获取第{page + 1}页数据")
        url = f"https://b2b-news.10jqka.com.cn/hxcota/market/stocks/v2/list?stock={stock}&market={market}&type=1&accessKey=74f9abd518ab0970&page={page}&pageSize=250"
        print(f"url:{url}")
        count = 0
        response =None
        while True and count < 3:
            try:
                response = requests.get(url)
                break
            except Exception as e:
                print(f"error,请求url异常,{e}")
                count += 1
        if not response:
            raise Exception("请求url异常")

        if response.status_code == 200:
            response_text = json.loads(response.text)
            if 'data' in response_text:
                length = len(response_text['data'])
                print(f"获取到{length}条数据")
                print("----------------")
                print("\n")
                if length == 0:
                    print(f"原因：{'' if 'msg' not in response_text else response_text['msg']}")
                    break
                storageList: list[Document] = []
                esDocList: list = []
                for pre_data in response_text['data']:
                    try:
                        total += 1
                        print(f"开始处理第【{total}】条数据")
                        digest = '' if 'digest' not in pre_data else pre_data['digest']
                        uniqueId = '' if 'unique' not in pre_data else pre_data['unique']
                        url = '' if 'url' not in pre_data else pre_data['url']
                        sourceUrl = '' if 'sourceUrl' not in pre_data else pre_data['sourceUrl']
                        detailUrl = '' if 'detailUrl' not in pre_data else pre_data['detailUrl']
                        print(f"digest:{digest}")
                        print(f"unique:{uniqueId}")
                        print(f"url:{url}")
                        print(f"sourceUrl:{sourceUrl}")
                        print(f"detailUrl:{detailUrl}")
                        if len(uniqueId) > 0:
                            id = uniqueId.split("_")[-1]
                            if len(id) > 0:
                                detail_url = f"https://b2b-news.10jqka.com.cn/hxcota/common/info/detail?id={id}&type=1&accessKey=74f9abd518ab0970"
                                print(f"detail_url:{detail_url}")
                                response_detail = requests.get(detail_url)
                                if response_detail.status_code == 200:
                                    response_detail_text = json.loads(response_detail.text)
                                    if 'data' in response_detail_text:
                                        data = response_detail_text['data']
                                        itemId = '' if 'itemId' not in data else data['itemId']  # 资讯id
                                        title = '' if 'title' not in data else data['title']  # 标题
                                        abstract = '' if 'abstract' not in data else data['abstract']  # 摘要
                                        content = '' if 'content' not in data else data['content']  # content
                                        time = '' if 'time' not in data else data['time']  # 创建时间
                                        contentUrl = '' if 'contentUrl' not in data else data['contentUrl']  # 跳转链接
                                        sourceUrls = '' if 'sourceUrls' not in data else data['sourceUrls']  # 源网地址
                                        source = '' if 'source' not in data else data['source']  # 来源
                                        stockInfo = '' if 'stockInfo' not in data else data['stockInfo']  # 相关个股
                                        try:
                                            soup = BeautifulSoup(content, features="html.parser")
                                            content = soup.get_text()
                                        except:
                                            print("解析异常，获取原有内容")

                                        print(f"资讯id-itemId:{itemId}")
                                        print(f"标题-title:{title}")
                                        print(f"摘要-abstract:{abstract}")
                                        print(f"创建时间-time:{time}")
                                        print(f"来源-source:{source}")
                                        print(f"源网地址-sourceUrls:{sourceUrls}")
                                        print(f"跳转链接-contentUrl:{contentUrl}")
                                        print(f"内容-content:{content}")
                                        print(f"相关个股-stockInfo:{stockInfo}")
                                        s_date = time
                                        try:
                                            s_date = datetime.datetime.fromtimestamp(int(time)).strftime(
                                                '%Y-%m-%d %H:%M:%S')
                                        except:
                                            print("发布时间解析异常，")
                                            s_date = time
                                        createTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        # 写入矢量库
                                        metadata = {"source": "API",
                                                    "uniqueId": uniqueId,
                                                    "code": stock,
                                                    "url": url,
                                                    "date": s_date,
                                                    "type": "资讯",
                                                    "createTime": createTime,
                                                    "abstract": abstract,
                                                    "title": title}
                                        doc = Document(page_content=content,
                                                       metadata=metadata)
                                        storageList.append(doc)
                                        # 写入到es
                                        es_doc= {'text':content}
                                        es_doc.update(metadata)
                                        esDocList.append(es_doc)

                        print(f"第{total}条数据处理完成")
                        print("\n")
                    except Exception as e:
                        print(
                            f"获取第【{total}】条数据,title:{title},url:{url}时异常，异常信息：{e}")
                # 存入矢量库
                if len(storageList) > 0:
                    store(storageList)
                # 存入es库
                if len(esDocList)>0:
                    esBatch(esDocList)
                page += 1
                print(f"第{page}页数据内容获取完毕")

            if 'hasNext' in response_text and not response_text['hasNext']:
                print("hasNext==False，跳出循环")
                break

    print(f"========获取【{stock}】在【{marketMap[market]}】的数据完毕，一共获取到【{total}】条数据")


###################### 存储类 ###############################################

import torch
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Milvus
from langchain.text_splitter import RecursiveCharacterTextSplitter

embedding_model_dict = {
    "ernie-tiny": "nghuyong/ernie-3.0-nano-zh",
    "ernie-base": "nghuyong/ernie-3.0-base-zh",
    "text2vec-base": "shibing624/text2vec-base-chinese",
    "text2vec": "/root/model/text2vec-large-chinese",
    "m3e-small": "moka-ai/m3e-small",
    "m3e-base": "moka-ai/m3e-base",
}
EMBEDDING_MODEL = "text2vec"
EMBEDDING_DEVICE = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"


def load_and_split(docs: list[Document]) -> list[Document]:
    print("进入切词阶段")
    """Load documents and split into chunks."""
    _text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    related_docs = _text_splitter.split_documents(docs)
    return [doc for doc in related_docs if len(doc.page_content.strip()) > 50]


def store(docs: list[Document]):
    docs = load_and_split(docs)
    print("进入存储阶段")
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model_dict[EMBEDDING_MODEL],
                                       model_kwargs={'device': EMBEDDING_DEVICE})
    count = 0
    obj = None
    while True and count < 3:
        try:
            obj = Milvus.from_documents(
                docs,
                embeddings,
                connection_args={"host": "8.217.52.63", "port": "19530"},
                collection_name="aifin",
            )
            break
        except Exception as e:
            print(f"error,写入矢量库异常,{e}")
            count += 1
    if not obj:
        raise Exception("写入矢量库异常")
    print("写入矢量库over")

###################### es操作 ###############################################
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
# 连接到Elasticsearch实例
def esBatch(docList:list):
    es = Elasticsearch(['172.28.84.188:9200'])
    #es = Elasticsearch("http://192.168.1.1:9200", http_auth=('username', 'password'), timeout=20)
    index_name = 'aifin'
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
    print("写入ES库over")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        stock = sys.argv[1]  # 域名
        if stock.startswith("6"):
            buildMarketdata(stock, 16)
        else:
            buildMarketdata(stock, 32)
    else:
        for stock in stockMap:
            if stock.startswith("6"):
                buildMarketdata(stock, 16)
            else:
                buildMarketdata(stock, 32)
