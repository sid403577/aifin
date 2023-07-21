

#############################FaissStore存储####################################
import os
import uuid
import torch
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS

from langchain.docstore.document import Document

EMBEDDING_DEVICE = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

# 知识检索内容相关度 Score, 数值范围约为0-1100，如果为0，则不生效，经测试设置为小于500时，匹配结果更精准
VECTOR_SEARCH_SCORE_THRESHOLD = 0
# 知识库默认存储路径
KB_ROOT_PATH = "/data/store/knowledge_base"
# 匹配后单段上下文长度
CHUNK_SIZE = 250

def temp_vector_store(vs_path, embeddings):
    temp_vs_path = os.path.join(KB_ROOT_PATH, vs_path, "vector_store")
    os.makedirs(temp_vs_path)
    if os.path.isdir(vs_path) and "index.faiss" in os.listdir(vs_path):
        return FAISS.load_local(temp_vs_path, embeddings)
    docs = [Document(page_content="test", metadata={"source": "test", "url": "test"})]
    return FAISS.from_documents(docs, embeddings)

def store(docs:list[Document]):
    embeddings = HuggingFaceEmbeddings(model_name="/data/aifin/huggingface/GanymedeNil/text2vec-large-chinese",
                                       model_kwargs={'device': EMBEDDING_DEVICE})
    tmp_vs_path = str(uuid.uuid4())
    vector_store = temp_vector_store(tmp_vs_path, embeddings)
    vector_store.chunk_size = CHUNK_SIZE
    vector_store.chunk_conent = True
    vector_store.score_threshold = VECTOR_SEARCH_SCORE_THRESHOLD
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=0)
    text_docs = text_splitter.split_documents(docs)
    vector_store.add_documents(text_docs)

#############################读取ES####################################
from elasticsearch import Elasticsearch
def readFromES(code:str)->list[Document]:
    es = Elasticsearch(['8.217.110.233:9200'])
    #es = Elasticsearch(['172.28.84.188:9200'])
    index_name = 'aifin'
    if es.indices.exists(index=index_name):
        page = 0
        size = 500
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
            print(f"length：{length}")
            if length>0:
                print(f"length>0")
                storageList: list[Document] = []
                if len(items)>0:
                    for item in items:
                        data = item['_source']
                        text = data.pop('text')
                        doc = Document(page_content=text,
                                       metadata=data)
                        storageList.append(doc)
                store(storageList)
                page+=1
            else:
                print(f"length=0")
                break

if __name__ == '__main__':
    readFromES('002594')
