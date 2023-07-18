

#############################FaissStore存储####################################
import os
import uuid
import torch
from elasticsearch import Elasticsearch
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS

from langchain.docstore.document import Document
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
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model_dict[EMBEDDING_MODEL],
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
def readFromES(code:str)->list[Document]:
    es = Elasticsearch(['8.217.110.233:9200'])
    #es = Elasticsearch(['172.28.84.188:9200'])
    index_name = 'aifin'
    if es.indices.exists(index=index_name):
        query = {
            "query": {
                "match": {
                    "code": code
                }
            }
        }
        allDoc = es.search(index=index_name, body=query)
        items = allDoc['hits']['hits']
        #print([i['_source'] for i in items])
        print(len(items))
        storageList: list[Document] = []
        if len(items)>0:
            for item in items:
                data = item['_source']
                text = data.pop('text')
                doc = Document(page_content=text,
                               metadata=data)
                storageList.append(doc)
        return storageList

if __name__ == '__main__':
    storageList = readFromES('002594')
    store(storageList)