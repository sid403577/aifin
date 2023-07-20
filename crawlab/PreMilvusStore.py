import sys
import uuid

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
    #"text2vec": "/data/aifin/huggingface/GanymedeNil/text2vec-large-chinese",
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


def store(docs: list[Document],code:str):
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
                collection_name=f"aifin_{code}",
            )
            break
        except Exception as e:
            print(f"error,写入矢量库异常,{e}")
            count += 1
    if not obj:
        raise Exception("写入矢量库异常")
    print("写入矢量库over")


#############################读取ES####################################
from elasticsearch import Elasticsearch
def readFromES(code:str)->list[Document]:
    es = Elasticsearch(['8.217.110.233:9200'])
    #es = Elasticsearch(['172.28.84.188:9200'])
    index_name = 'aifin'
    if es.indices.exists(index=index_name):
        page = 0
        size = 200
        while True:
            print(f"page:{page}")
            query = {
                "query": {
                    "match": {
                        "code": code
                    }
                },
                "from":page*size, # 分页开始的位置，默认为0
                "size":size,# 期望获取的文档总数
            }
            allDoc = es.search(index=index_name, body=query)
            items = allDoc['hits']['hits']
            #print([i['_source'] for i in items])
            length = len(items)
            print(f"length：{length}，items：{items}")
            if length>0:
                print(f"length>0")
                storageList: list[Document] = []
                if len(items)>0:
                    for item in items:
                        data = item['_source']
                        metadata = {"source": '' if ('source' not in data or not data['source']) else data['source'],
                                    "uniqueId": uuid.uuid1() if ('uniqueId' not in data or not data['uniqueId']) else data['uniqueId'],
                                    "code": '' if ('code' not in data or not data['code']) else data['code'],
                                    "url": '' if ('url' not in data or not data['url']) else data['url'],
                                    "date": '' if ('date' not in data or not data['date']) else data['date'],
                                    "type": '' if ('type' not in data or not data['type']) else data['type'],
                                    "createTime": '' if ('createTime' not in data or not data['createTime']) else data['createTime'],
                                    "abstract": '' if ('abstract' not in data or not data['abstract']) else data['abstract'],
                                    "title": '' if ('title' not in data or not data['title']) else data['title']}
                        doc = Document(page_content='' if ('text' not in data or not data['text']) else data['text'],
                                       metadata=metadata)
                        storageList.append(doc)
                store(storageList,code)
                page+=1
            else:
                print(f"length=0")
                break


if __name__ == '__main__':
    code = sys.argv[1]  # 股票代码
    readFromES(code)