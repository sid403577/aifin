# 获取单只股票的数据
import datetime
import json
import sys

import requests
from bs4 import BeautifulSoup

marketMap = {
    48: "新同花顺指数",
    32: "深圳证券交易所",
    16: "上海证券交易所",

    104: "申万指数",
    144: "三板市场",
    176: "香港联交所",
    168: "纽约交易所",
    184: "纳斯达克",
}


def buildMarketdata(stock: str, market: int):
    import csv
    # from crawlab import save_item
    csv_file = open(f"/data/api_2_comments_data_{stock}_{market}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv",
                    'a+',
                    newline='', encoding='utf-8-sig')  # 解决中文乱码问题。a+表示向csv文件追加
    writer = csv.writer(csv_file)
    writer.writerow(['id','date', 'title', 'content', ])

    page = 0
    total = 0
    print(f"========开始获取【{stock}】在【{marketMap[market]}】的数据")
    while True:
        print(f"开始获取第{page + 1}页数据")
        url = f"https://b2b-news.10jqka.com.cn/hxcota/market/stocks/v2/list?stock={stock}&market={market}&type=1&accessKey=74f9abd518ab0970&page={page}&pageSize=250"
        print(f"url:{url}")
        response = requests.get(url)
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
                for pre_data in response_text['data']:
                    try:
                        total += 1
                        print(f"开始处理第【{total}】条数据")
                        digest = '' if 'digest' not in pre_data else pre_data['digest']
                        unique = '' if 'unique' not in pre_data else pre_data['unique']
                        url = '' if 'url' not in pre_data else pre_data['url']
                        sourceUrl = '' if 'sourceUrl' not in pre_data else pre_data['sourceUrl']
                        detailUrl = '' if 'detailUrl' not in pre_data else pre_data['detailUrl']
                        print(f"digest:{digest}")
                        print(f"unique:{unique}")
                        print(f"url:{url}")
                        print(f"sourceUrl:{sourceUrl}")
                        print(f"detailUrl:{detailUrl}")
                        if len(unique) > 0:
                            id = unique.split("_")[-1]
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
                                        # 写入csv文件
                                        result_item1 = [total,s_date, title, content]
                                        writer.writerow(result_item1)  # 原来的链接不全因此给他补齐
                                        # 写入矢量库
                                        doc = Document(page_content=content,
                                                       metadata={"source": "API",
                                                                 "code": stock,
                                                                 "url": url,
                                                                 "date": s_date,
                                                                 "type": "资讯",
                                                                 "from": marketMap[market],
                                                                 "createTime": createTime,
                                                                 "title": title})
                                        storageList.append(doc)
                        print(f"第{total}条数据处理完成")
                        print("\n")
                    except Exception as e:
                        print(
                            f"获取第【{total}】条数据,title:{title},url:{url}时异常，异常信息：{e}")
                # 存入矢量库
                if len(storageList) > 0:
                    store(storageList)
                page += 1
                print(f"第{page}页数据内容获取完毕")

            if 'hasNext' in response_text and not response_text['hasNext']:
                print("hasNext==False，跳出循环")
                break

    print(f"========获取【{stock}】在【{marketMap[market]}】的数据完毕，一共获取到【{total}】条数据")
    csv_file.close()


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
    while True and count < 3:
        try:
            Milvus.from_documents(
                docs,
                embeddings,
                connection_args={"host": "8.217.52.63", "port": "19530"},
                collection_name="tonghuashun_2",
            )
            break
        except Exception as e:
            print(f"error,写入矢量库异常,{e}")
            count += 1

    print("over")


if __name__ == '__main__':
    stock = sys.argv[1]  # 域名
    for market in marketMap:
        buildMarketdata(stock, market)
