import csv

from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.vectorstores import FAISS
from vectorstores import MyFAISS, MyMilvus

codes = ['002594', '000063']
column = 'text'
query = '比亚迪'


def load_file(file_path):
    with open(file_path, newline="") as csvfile:
        csv_reader = csv.DictReader(csvfile)  # type: ignore
        for i, row in enumerate(csv_reader):
            if row['code'] in codes:
                yield row['abstract']


if __name__ == "__main__":
    embeddings = HuggingFaceEmbeddings(model_name='GanymedeNil/text2vec-large-chinese',
                                       model_kwargs={'device': 'cpu'})
    n = 1
    max = 200
    docs = []
    chunk_size = 1000
    for text in load_file("./test.csv"):
        if n > max:
            break
        n += 1
        print(f" ======================================================")
        print("source:", len(text))
        print(text)

        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=0)
        texts = splitter.split_text(text)
        m = 1
        for t in texts:
            print(f"splitter {m} {len(t)}: {t}")
            m += 1
        docs += [Document(page_content=t) for t in texts]

    vs = MyFAISS.from_documents(docs, embeddings)
    print("myfaiss searching", len(docs))
    ret_docs = vs.similarity_search_with_score(query, 10)
    print("myfaiss searched", len(ret_docs))
    for doc in ret_docs:
        score = doc.metadata['score']
        print(f"{score} {doc.page_content}")

    vs = FAISS.from_documents(docs, embeddings)
    print("faiss searching", len(docs))
    ret_docs = vs.similarity_search_with_score(query, 10)
    print("faiss searched", len(ret_docs))
    for s in ret_docs:
        doc = s[0]
        score = s[1]
        print(f"{score} {doc.page_content}")

    # vector_db = MyMilvus(
    #     embeddings,
    #     collection_name='cgf' + str(chunk_size),
    # )
    # vector_db.add_documents(docs)
    # print("milvus searching", len(docs))
    # ret_docs = vector_db.similarity_search_with_score(query, 10)
    # print("milvus searched", len(ret_docs))
    # for doc in ret_docs:
    #     score = doc.metadata['score']
    #     print(f"{score} {doc.page_content}")
