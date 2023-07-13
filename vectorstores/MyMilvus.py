import time

import environs
from langchain.document_loaders import UnstructuredFileLoader
from langchain.vectorstores import Milvus
from langchain.vectorstores.base import VectorStore
from langchain.docstore.document import Document
from typing import Callable, Any, List, Optional
from configs.model_config import *
from langchain.embeddings.huggingface import HuggingFaceEmbeddings


class MyMilvus(Milvus, VectorStore):
    def __init__(
            self,
            embedding_function: Callable,
            collection_name: str = "LangChainCollection"
    ):
        s = time.perf_counter()
        print(f"load milvus ...")
        super().__init__(embedding_function=embedding_function,
                         collection_name=collection_name, connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT})
        self.score_threshold = VECTOR_SEARCH_SCORE_THRESHOLD
        self.chunk_size = CHUNK_SIZE
        self.chunk_conent = False
        elapsed = time.perf_counter() - s
        print(f"load milvus {elapsed:0.2f} seconds")

    def similarity_search_with_score_by_vector(
            self,
            embedding: List[float],
            k: int = 4,
            param: Optional[dict] = None,
            expr: Optional[str] = None,
            timeout: Optional[int] = None,
            **kwargs: Any,
    ) -> List[Document]:
        ret = super().similarity_search_with_score_by_vector(embedding, k, param, expr, timeout, **kwargs)
        docs = []
        for item in ret:
            doc = item[0]
            doc.metadata["score"] = int(item[1])
            docs.append(doc)
        return docs

    def delete_doc(self, source: str or List[str]):
        return f"docs delete fail"
        return f"docs delete success"

    def update_doc(self, source, new_docs):
        return f"docs update fail"
        return f"docs update success"

    def list_docs(self):
        return list()
        # from pymilvus import connections, utility
        # if not connections.has_connection(environs.Env().str("MILVUS_CONN_ALIAS", "default")):
        #     connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        #
        # # 指定集合名称和标量字段名称
        # collection_name = self.collection_name
        # field_name = 'source'
        # response = connections.distinct(collection_name, field_name)
        # # 提取指定字段的去重值
        # unique_values = set(result[field_name] for result in response)
        # return unique_values

    def save(self):
        if self.col:
            self.col.flush()

    @staticmethod
    def has_collection(collection_name: str) -> bool:
        from pymilvus import utility, connections
        if not connections.has_connection(environs.Env().str("MILVUS_CONN_ALIAS", "default")):
            connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        has = utility.has_collection(collection_name)
        return has


if __name__ == "__main__":
    embeddings = HuggingFaceEmbeddings(model_name='../huggingface/GanymedeNil/text2vec-large-chinese',
                                       model_kwargs={'device': 'cpu'})
    r = MyMilvus(embedding_function=embeddings, collection_name="test")
    loader = UnstructuredFileLoader(__file__, mode="elements")
    r.add_documents(loader.load())
    print(r)
