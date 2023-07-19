import csv
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from configs.model_config import KB_ROOT_PATH
from vectorstores import MyFAISS
import os
os.environ["OPENAI_API_KEY"] = "sk-kcfJcDXKztSEuMxaSqVjvuniMFIlz8HSr2xApuxivkNINiEc" #当前key为内测key，内测结束后会失效，在群里会针对性的发放新key
os.environ["OPENAI_API_BASE"] = "https://key.langchain.com.cn/v1"
os.environ["OPENAI_API_PREFIX"] = "https://key.langchain.com.cn"

def save_faiss(code, embeddings, chunk_size=100, debug=True):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=0)
    content_path = os.path.join(KB_ROOT_PATH, code, "content")
    if not os.path.exists(content_path):
        os.makedirs(content_path)
    vs_path = os.path.join(KB_ROOT_PATH, code, "vector_store")
    if not os.path.exists(vs_path):
        os.makedirs(vs_path)
    docs = []
    with open('./test.csv', newline="") as csvfile:
        csv_reader = csv.DictReader(csvfile)  # type: ignore
        for i, row in enumerate(csv_reader):
            if row['code'] == code:
                text = row['abstract']
                print(type(text))
                if debug:
                    print(f"source: {len(text)}")
                    print(f"{text}")
                uniqueId = row['uniqueId']
                file_path = os.path.join(content_path, uniqueId)
                if os.path.exists(file_path) and os.path.getsize(file_path) == len(text):
                    print(f"文件 {file_path} 已存在。")
                    break
                texts = splitter.split_text(text)
                if debug:
                    for t in texts:
                        print(f"splitter {len(texts)} ===: {t}")
                docs += [Document(page_content=t) for t in texts]
                with open(file_path, "wb") as f:
                    f.write(text.encode())
                    f.flush()
    if docs:
        vs = MyFAISS.from_documents(docs, embeddings)
        vs.save_local(vs_path)

if __name__ == "__main__":
    embeddings = HuggingFaceEmbeddings(model_name='../huggingface/GanymedeNil/text2vec-large-chinese',
                                       model_kwargs={'device': 'cpu'})
    stockMap = {
        "002594": "比亚迪",
        "600887": "伊利股份",
        "300750": "宁德时代",
        "002518": "科士达",
        "600225": "卓朗科技",
        "600977": "中国电影",
        "603259": "药明康德",
        "000063": "中兴通讯",
        "600737": "中粮糖业",
        "300887": "谱尼测试",
    }

    for code, name in stockMap.items():
        save_faiss(code, embeddings, chunk_size=100, debug=True)
