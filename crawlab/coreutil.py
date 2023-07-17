###################### 获取数据 ###############################################

import datetime
import json
import re
import sys
import urllib.parse

import chardet
import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter

normalUrl = "https://api.crawlbase.com/?token=mjBM5V0p5xIDxV1N9MqYpg"

htmlcontent = {
    "search-api-web.eastmoney.com": {
        "domainurl": "https://search-api-web.eastmoney.com/search/jsonp?cb=jQuery35107761762966427765_1687662386467",
        "parse_param": {
            "key": "param",
            "value": '{"uid": "4529014368817886", "keyword": "$code", "type": ["cmsArticleWebOld"], "client": "web", "clientType": "web", "clientVersion": "curr", "param": {"cmsArticleWebOld": {"searchScope": "default", "sort": "time", "pageIndex": $pageIndex, "pageSize": $pageSize, "preTag": "<em>", "postTag": "</em>"}}}',
        },
        "result_re": 'jQuery35107761762966427765_1687662386467\((.*)\)',
        "data": ['result', 'cmsArticleWebOld'],
        "text_re": {
            "element": "div",
            #"attr": {"class": "article"},
            "attr": {"class": "txtinfos"},
        }

    }
}


def download_page(url, para=None):
    crawUrl = f"{normalUrl}&url={urllib.parse.quote(url)}"
    if para:
        response = requests.get(crawUrl, params=para)
    else:
        response = requests.get(crawUrl)
    if response.status_code == 200:
        # 以下为乱码异常处理
        try:
            code1 = chardet.detect(response.content)['encoding']
            text = response.content.decode(code1)
        except:
            code = response.encoding
            try:
                text = response.text.encode(code).decode('utf-8')
            except:
                try:
                    text = response.text.encode(code).decode('gbk')
                except:
                    text = response.text
        return text
    else:
        print("failed to download the page")


def eastmoney(domain: str, code: str, type: str, startPage=1):  # 两个参数分别表示开始读取与结束读取的页码

    param_content = htmlcontent[domain]
    if not param_content:
        print(f"该域名数据无法获取，domain:{domain}")
        return

    # 遍历每一个URL
    total = 0
    pageIndex = startPage
    pageSize = 10
    flag = True
    count = 0;
    while flag and count < 5:
        print(f"开始获取第{pageIndex}页数据")
        domainurl: str = param_content['domainurl']
        domainurl = domainurl.replace("$code", code).replace("$pageIndex", str(pageIndex)).replace("$pageSize",
                                                                                                   str(pageSize))
        parse_param = param_content['parse_param']
        link = f"{domainurl}"
        if parse_param:
            key = parse_param['key']
            value: str = parse_param['value']
            value = value.replace("$code", code).replace("$pageIndex", str(pageIndex)).replace("$pageSize",
                                                                                               str(pageSize))
            link = link + "&" + key + "=" + urllib.parse.quote(value)

        print(f"link:{link}")  # 用于检查
        crawUrl = f"{normalUrl}&url={urllib.parse.quote(link)}"
        try:
            response = requests.get(crawUrl, verify=False, timeout=30)  # 禁止重定向
            print(response.text)
        except:
            count += 1
            continue
        content = response.text
        if 'result_re' in param_content:
            content = re.findall(param_content['result_re'], response.text)[0]
        # 读取的是json文件。因此就用json打开啦
        data = json.loads(content)
        # 找到原始页面中数据所在地
        for pre in param_content['data']:
            data = data[pre]

        print(f"获取第{pageIndex}页的数据，大小为{len(data)}")
        storageList: list[Document] = []
        esDocList: list = []
        for i in range(0, len(data)):

            try:
                date = data[i]['date']
                if type == "1":
                    s_date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').date()
                    Yesterday = datetime.date.today() - datetime.timedelta(days=1)
                    if s_date < Yesterday:
                        print(f"昨天的数据已经处理完成，跳出循环")
                        flag = False
                        break

                total += 1
                print(f"开始处理第{total}条数据：{data[i]}")
                # 数据处理
                print(f"获取第{total}条数据的link内容：{link}")
                url = data[i]['url']
                abstract = data[i]['content']
                text = get_text(url, param_content['text_re'])
                title = data[i]['title']
                uniqueId = data[i]['code']
                createTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if abstract:
                    abstract = abstract.replace('</em>', '').replace('<em>', '').split()
                if text:
                    text = text.replace('</em>', '').replace('<em>', '').split()
                else:
                    text = abstract
                if title:
                    title = title.replace('</em>', '').replace('<em>', '').split()


                print(f"uniqueId:{uniqueId}")
                print(f"code:{code}")
                print(f"url:{url}")
                print(f"date:{date}")
                print(f"type:{type}")
                print(f"text:{text}")
                print(f"abstract:{abstract}")
                print(f"title:{title}")

                metadata = {"source": "Web",
                            "uniqueId": uniqueId,
                            "code": code,
                            "url": url,
                            "date": date,
                            "type": "东方财富-资讯",
                            "createTime": createTime,
                            "abstract": abstract,
                            "title": title}
                # 写入矢量库
                doc = Document(page_content=text,metadata=metadata)
                storageList.append(doc)
                # 写入到es
                es_doc = {'text': content}
                es_doc.update(metadata)
                esDocList.append(es_doc)

                print(f"第{total}条数据处理完成")

            except Exception as e:
                print(
                    f"获取第【{pageIndex}】页的第【{i}】条数据,title:{data[i]['title']},url:{data[i]['url']}时异常，异常信息：{e}")
        # 存入矢量库
        if len(storageList) > 0:
            store(storageList)
        # 存入es库
        if len(esDocList) > 0:
            esBatch(esDocList)

        print(f"第{pageIndex}页数据处理完成")
        if len(data) < pageSize:
            break
        pageIndex += 1
        count=0

    print(f"处理完成，从{startPage}-{pageIndex}页，一共处理{total}条数据")


def get_text(url, text_re: dict):
    soup = BeautifulSoup(download_page(url))
    all_comments = soup.find_all(text_re['element'], text_re['attr'])
    if all_comments and len(all_comments) > 0:
        text1 = all_comments[0]
        con = text1.get_text()  # 只提取文字
    else:
        con = soup.get_text()
    return con


###################### 存储类 ###############################################

import torch
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Milvus

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
    """Load documents and split into chunks."""
    _text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
    related_docs = _text_splitter.split_documents(docs)
    return [doc for doc in related_docs if len(doc.page_content.strip()) > 20]


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


if __name__ == "__main__":
    domain = sys.argv[1]  # 域名
    code = sys.argv[2]  # 股票代码
    type = sys.argv[3]  # 增量1，全量2
    startPage = sys.argv[4]  # 从第几页
    print(f"参数列表，domain:{domain},code:{code},type:{type},startPage:{startPage}")
    eastmoney(domain, code, type, int(startPage))
    #eastmoney("search-api-web.eastmoney.com", "002594", "2", 1)
