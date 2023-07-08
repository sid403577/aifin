from typing import List, Optional

import torch
from langchain.docstore.document import Document
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain.vectorstores import Milvus
from langchain.text_splitter import TextSplitter, CharacterTextSplitter

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
def load() -> List[Document]:
    docs=[]
    content="近日，网传今年2月份抢教授话筒的蒋同学高考655分，被哈工大录取。对此，7月6日，哈尔滨工业大学招生办工作人员回应称，录取还没开始，各省尚未投档，投档结束了才知道，录取时间可能在20日左右。"
    source="https://mbd.baidu.com/newspage/data/landingsuper?context=%7B%22nid%22%3A%22news_9605400130597382296%22%7D&n_type=-1&p_from=-1"
    doc = Document(page_content=content,
                   metadata={"source": source,
                             "date":"2022-09-10 12:20:20",
                             "title":"高考"})
    docs.append(doc)
    return docs

def load_and_split(docs:list[Document]) -> list[Document]:
    """Load documents and split into chunks."""
    _text_splitter = CharacterTextSplitter(
        separator="  ",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    return _text_splitter.split_documents(docs)

def store(docs:list[Document]):
    docs = load_and_split(docs)
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model_dict[EMBEDDING_MODEL],
                                                model_kwargs={'device': EMBEDDING_DEVICE})
    vector_db = Milvus.from_documents(
        docs,
        embeddings,
        connection_args={"host": "8.217.52.63", "port": "19530"},
    )
    docs = vector_db.similarity_search("蒋同学高考")
    if docs and len(docs)>0:
        content =[doc.page_content for doc in docs]
        print(content)
    print("over")


if __name__ == '__main__':
    store(load())






