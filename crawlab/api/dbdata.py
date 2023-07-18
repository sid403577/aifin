import datetime

import pyodbc

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
    "text2vec": "D://develop/model/text2vec-large-chinese",
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


def store(docs: list[Document],skip_count:int):
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
            print(f"error,写入矢量库异常,{e},{skip_count}")
            count += 1
    if not obj:
        print(f"error,写入矢量库异常,{skip_count}")
        raise Exception("写入矢量库异常"+skip_count)
    print("over")

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
# 连接到Elasticsearch实例
def esBatch(docList:list,security_code:str):
    es = Elasticsearch(['8.217.110.233:9200'])
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
    while True and count < 3:
        try:
            bulk(es, actions)
            break
        except Exception as e:
            print(f"error,写入es异常,{e}")
            count += 1
    print(f"success,写入成功."+security_code)
    bulk(es, actions)


def transEs(security_code:str):
    # Set up the SQL Server connection
    server = '36.137.180.195,24857'
    database = 'emdata'
    username = 'emdata'
    password = 'emdata'

    connection_string = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    # 定义每页的大小和页码
    page_size = 500
    page_number = 1
    # 计算要跳过的记录数量
    skip_count = (page_number - 1) * page_size
    # skip_count = 2
    has_more_results = True
    while has_more_results:
        query = f"""
            SELECT 'DB' as source,
                   a.SECURITYCODE as code,
                   a.EID as uniqueId,
                   '研报' as type,
                   a.COLUMNNAME as reTypeName,
                   a.SOURCEURL as url,
                   a.REPORTTITLE as title,
                   a.PUBLISHDATE as date,
                   a.SRATINGNAME as rawTating,
                   a.COMPANYNAME as comeName,
                   b.SEARCHCONTENT as abstract,
                   b.INFOBODYCONTENT as text
            FROM INFO_RE_BASINFOCOM a
            JOIN INFO_RE_CONTENTCOM b ON a.INFOCODE = b.INFOCODE
            WHERE a.SECURITYCODE = '{security_code}'
            and a.PUBLISHDATE > '2020-01-01 00:00:00'
            ORDER BY a.PUBLISHDATE DESC
            OFFSET {skip_count} ROWS FETCH NEXT {page_size} ROWS ONLY
            """
        cursor.execute(query)
        results = cursor.fetchall()  # Retrieve 500 records at a time

        if not results:
            has_more_results = False
            break
        else:
            page_number = page_number+1
            skip_count = (page_number - 1) * page_size
            # if skip_count == 1:
            #     break;
            # skip_count = 1
        storageList: list[Document] = []
        esDocList: list = []
        for row in results:
            metadata = {
                'source': row.source,
                'code': row.code,
                'uniqueId': f"{row.uniqueId}",
                'type': row.type,
                'reTypeName': row.reTypeName,
                'url': row.url if row.url is not None else "",
                'title': row.title,
                'date': row.date,
                'createTime': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'rawTating': row.rawTating if row.rawTating is not None else "",
                'comeName': row.comeName,
                'abstract': row.abstract,
            }
            content = row.text
            doc = Document(page_content=content,
                           metadata=metadata)
            storageList.append(doc)
            # 写入到es
            es_doc = {'text': content}
            es_doc.update(metadata)
            print(es_doc)
            esDocList.append(es_doc)

        if len(storageList) > 0:
            store(storageList,skip_count)
            # 存入es库
        # if len(esDocList) > 0:
        #     esBatch(esDocList,security_code)

    # Close the connections
    cursor.close()
    conn.close()




if __name__ == '__main__':
    security_code = [
		'300750',
		'002518',
		'600225',
		'600977',
		'603259',
		'300887',
		'002967',
		'002465',
		'000063',
		'600737',
		'605196',
		'300661',
		'688536',
		'060030',
		'300418',
		'002722',
		'688312',
		'03988']
    for row in security_code:
        docs = transEs(row)
