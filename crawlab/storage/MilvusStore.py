###################### 存储类 ###############################################
import copy

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
    """Load documents and split into chunks."""
    _text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
    related_docs = _text_splitter.split_documents(docs)
    return [doc for doc in related_docs if len(doc.page_content.strip()) > 20]


def storeData(docs: list[dict],collection_name:str,path:str):
    docList:list[Document] = []
    for doc in copy.deepcopy(docs):
        text = '' if 'text' not in doc else doc.pop("text")
        docx = Document(page_content=text,
                       metadata=doc)
        docList.append(docx)

    docs = load_and_split(docList)
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
                connection_args={"host": path.split(":")[0], "port": path.split(":")[1]},
                collection_name=collection_name,
            )
            break
        except Exception as e:
            print(f"error,写入矢量库异常,{e}")
            count += 1
    if not obj:
        raise Exception("写入矢量库异常")
    print(f"写入矢量库【{collection_name }】over")
