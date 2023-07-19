import datetime
import time
import shutil
from functools import lru_cache
from typing import List

from langchain import FewShotPromptTemplate, PromptTemplate
from langchain.docstore.document import Document
from langchain.document_loaders import UnstructuredFileLoader, TextLoader, CSVLoader
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.prompts.example_selector import SemanticSimilarityExampleSelector
from langchain.vectorstores import Chroma
from pypinyin import lazy_pinyin
from tqdm import tqdm

import models.shared as shared
from agent import google_search, bing_search
from configs.model_config import *
from loader import UnstructuredPaddleImageLoader, UnstructuredPaddlePDFLoader
from models.base import (BaseAnswer)
from models.loader import LoaderCheckPoint
from models.loader.args import parser
from textsplitter import ChineseTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from textsplitter.zh_title_enhance import zh_title_enhance
from utils import torch_gc, join_array_with_index, extract_question_and_keywords
from vectorstores import MyFAISS, MyMilvus
from langchain.vectorstores.base import VectorStore


# patch HuggingFaceEmbeddings to make it hashable
def _embeddings_hash(self):
    return hash(self.model_name)


HuggingFaceEmbeddings.__hash__ = _embeddings_hash


def has_vector_store(vs_path) -> bool:
    directories = vs_path.split("/")
    if MILVUS_HOST:
        if len(directories) > 1:
            vs_path = directories[-2]
        return MyMilvus.has_collection(vs_path)
    if len(directories) == 1:
        vs_path = os.path.join(KB_ROOT_PATH, vs_path, "vector_store")
    return vs_path is not None and os.path.exists(vs_path) and "index.faiss" in os.listdir(vs_path)


# will keep CACHED_VS_NUM of vector store caches
@lru_cache(CACHED_VS_NUM)
def load_vector_store(vs_path, embeddings):
    directories = vs_path.split("/")
    if MILVUS_HOST:
        if len(directories) > 1:
            vs_path = directories[-2]
        return MyMilvus(embeddings, vs_path)
    if len(directories) == 1:
        vs_path = os.path.join(KB_ROOT_PATH, vs_path, "vector_store")
    return MyFAISS.load_local(vs_path, embeddings)


def add_vector_store(vs_path, embeddings, docs):
    if MILVUS_HOST:
        directories = vs_path.split("/")
        if len(directories) > 1:
            vs_path = directories[-2]
        vector_store = MyMilvus(embeddings, vs_path)
        vector_store.add_documents(docs)
        torch_gc()
        vector_store.save()
        return vector_store
    if has_vector_store(vs_path):
        vector_store = MyFAISS.load_local(vs_path, embeddings)
        vector_store.add_documents(docs)
    else:
        vector_store = MyFAISS.from_documents(docs, embeddings)  # docs 为Document列表
    torch_gc()
    vector_store.save_local(vs_path)
    return vector_store


def tree(filepath, ignore_dir_names=None, ignore_file_names=None):
    """返回两个列表，第一个列表为 filepath 下全部文件的完整路径, 第二个为对应的文件名"""
    if ignore_dir_names is None:
        ignore_dir_names = []
    if ignore_file_names is None:
        ignore_file_names = []
    ret_list = []
    if isinstance(filepath, str):
        if not os.path.exists(filepath):
            print("路径不存在")
            return None, None
        elif os.path.isfile(filepath) and os.path.basename(filepath) not in ignore_file_names:
            return [filepath], [os.path.basename(filepath)]
        elif os.path.isdir(filepath) and os.path.basename(filepath) not in ignore_dir_names:
            for file in os.listdir(filepath):
                fullfilepath = os.path.join(filepath, file)
                if os.path.isfile(fullfilepath) and os.path.basename(fullfilepath) not in ignore_file_names:
                    ret_list.append(fullfilepath)
                if os.path.isdir(fullfilepath) and os.path.basename(fullfilepath) not in ignore_dir_names:
                    ret_list.extend(tree(fullfilepath, ignore_dir_names, ignore_file_names)[0])
    return ret_list, [os.path.basename(p) for p in ret_list]


def load_file(filepath, sentence_size=SENTENCE_SIZE, using_zh_title_enhance=ZH_TITLE_ENHANCE):
    if filepath.lower().endswith(".md"):
        loader = UnstructuredFileLoader(filepath, mode="elements")
        docs = loader.load()
    elif filepath.lower().endswith(".txt"):
        loader = TextLoader(filepath, autodetect_encoding=True)
        textsplitter = ChineseTextSplitter(pdf=False, sentence_size=sentence_size)
        docs = loader.load_and_split(textsplitter)
    elif filepath.lower().endswith(".pdf"):
        loader = UnstructuredPaddlePDFLoader(filepath)
        textsplitter = ChineseTextSplitter(pdf=True, sentence_size=sentence_size)
        docs = loader.load_and_split(textsplitter)
    elif filepath.lower().endswith(".jpg") or filepath.lower().endswith(".png"):
        loader = UnstructuredPaddleImageLoader(filepath, mode="elements")
        textsplitter = ChineseTextSplitter(pdf=False, sentence_size=sentence_size)
        docs = loader.load_and_split(text_splitter=textsplitter)
    elif filepath.lower().endswith(".csv"):
        loader = CSVLoader(filepath)
        docs = loader.load()
    else:
        loader = UnstructuredFileLoader(filepath, mode="elements")
        textsplitter = ChineseTextSplitter(pdf=False, sentence_size=sentence_size)
        docs = loader.load_and_split(text_splitter=textsplitter)
    if using_zh_title_enhance:
        docs = zh_title_enhance(docs)
    write_check_file(filepath, docs)
    return docs


def write_check_file(filepath, docs):
    folder_path = os.path.join(os.path.dirname(filepath), "tmp_files")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    fp = os.path.join(folder_path, 'load_file.txt')
    with open(fp, 'a+', encoding='utf-8') as fout:
        fout.write("filepath=%s,len=%s" % (filepath, len(docs)))
        fout.write('\n')
        for i in docs:
            fout.write(str(i))
            fout.write('\n')
        fout.close()


def generate_prompt(related_docs: List[str],
                    query: str,
                    prompt_template: str = PROMPT_TEMPLATE, ) -> str:

    context = "\n".join([doc.page_content for doc in related_docs])
    prompt = prompt_template.replace("{question}", query).replace("{context}", context)
    print(f"prompt: {prompt}")
    return prompt

def generate_few_shot_prompt(related_docs: List[str],
                    query: str, embeddings) -> str:
    example_selector = SemanticSimilarityExampleSelector.from_examples(
        # This is the list of examples available to select from.
        PROMPT_TEMPLATE_EXAMPLES,
        # This is the embedding class used to produce embeddings which are used to measure semantic similarity.
        embeddings,
        # This is the VectorStore class that is used to store the embeddings and do a similarity search over.
        Chroma,
        # This is the number of examples to produce.
        k=1
    )
    example_prompt = PromptTemplate(
        input_variables=["query", "answer"],
        template=PROMPT_TEMPLATE_EXAMPLE
    )
    few_shot_prompt_template = FewShotPromptTemplate(
        example_selector=example_selector,
        # examples = examples,
        example_prompt=example_prompt,
        prefix=PROMPT_TEMPLATE_EXAMPLE_PREFIX,
        suffix=PROMPT_TEMPLATE_EXAMPLE_SUFFIX,
        input_variables=["question", "context"],
        example_separator="\n\n"
    )

    context = "\n".join([doc.page_content for doc in related_docs])
    prompt = few_shot_prompt_template.format(question=query, context=context)
    print(f"prompt: {prompt}")
    return prompt


def search_result2docs(search_results):
    docs = []
    for result in search_results:
        content = None
        if "content" in result.keys():
            content = result["content"]
            if content:
                if len(content) > 100:
                    result["snippet"] = content[:100]
                else:
                    result["snippet"] = content

        if len(result["snippet"]) == 0:
            continue

        doc = Document(page_content=content if content else result["snippet"],
                       metadata={"url": result["link"] if "link" in result.keys() else "",
                                 "title": result["title"] if "title" in result.keys() else "",
                                 "source": 'online',
                                 "snippet": result["snippet"],
                                 })
        docs.append(doc)
    return docs


def company(query, chat_history=[]):
    company_name = ""
    for i, (old_query, response) in enumerate(chat_history):
        if old_query is None:
            continue
        for company in COMPANYS:
            if company in old_query:
                company_name = company
    for company in COMPANYS:
        if company in query:
            company_name = company
    return company_name


class LocalDocQA:
    llm: BaseAnswer = None
    embeddings: object = None
    top_k: int = VECTOR_SEARCH_TOP_K
    chunk_size: int = CHUNK_SIZE
    chunk_conent: bool = True
    score_threshold: int = VECTOR_SEARCH_SCORE_THRESHOLD

    def init_cfg(self,
                 embedding_model: str = EMBEDDING_MODEL,
                 embedding_device=EMBEDDING_DEVICE,
                 llm_model: BaseAnswer = None,
                 top_k=VECTOR_SEARCH_TOP_K,
                 ):
        self.llm = llm_model
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model_dict[embedding_model],
                                                model_kwargs={'device': embedding_device})
        self.top_k = top_k

    def init_knowledge_vector_store(self,
                                    filepath: str or List[str],
                                    vs_path: str or os.PathLike = None,
                                    sentence_size=SENTENCE_SIZE):
        loaded_files = []
        failed_files = []
        if isinstance(filepath, str):
            if not os.path.exists(filepath):
                print("路径不存在")
                return None
            elif os.path.isfile(filepath):
                file = os.path.split(filepath)[-1]
                try:
                    docs = load_file(filepath, sentence_size)
                    logger.info(f"{file} 已成功加载")
                    loaded_files.append(filepath)
                except Exception as e:
                    logger.error(e)
                    logger.info(f"{file} 未能成功加载")
                    return None
            elif os.path.isdir(filepath):
                docs = []
                for fullfilepath, file in tqdm(zip(*tree(filepath, ignore_dir_names=['tmp_files'])), desc="加载文件"):
                    try:
                        docs += load_file(fullfilepath, sentence_size)
                        loaded_files.append(fullfilepath)
                    except Exception as e:
                        logger.error(e)
                        failed_files.append(file)

                if len(failed_files) > 0:
                    logger.info("以下文件未能成功加载：")
                    for file in failed_files:
                        logger.info(f"{file}\n")

        else:
            docs = []
            for file in filepath:
                try:
                    docs += load_file(file)
                    logger.info(f"{file} 已成功加载")
                    loaded_files.append(file)
                except Exception as e:
                    logger.error(e)
                    logger.info(f"{file} 未能成功加载")
        if len(docs) > 0:
            logger.info("文件加载完毕，正在生成向量库")
            if not vs_path:
                vs_path = os.path.join(KB_ROOT_PATH,
                                       f"""{"".join(lazy_pinyin(os.path.splitext(file)[0]))}_FAISS_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}""",
                                       "vector_store")
            vector_store = add_vector_store(vs_path, self.embeddings, docs)
            return vs_path, loaded_files
        else:
            logger.info("文件均未成功加载，请检查依赖包或替换为其他文件再次上传。")
            return None, loaded_files

    def one_knowledge_add(self, vs_path, one_title, one_conent, one_content_segmentation, sentence_size):
        try:
            if not vs_path or not one_title or not one_conent:
                logger.info("知识库添加错误，请确认知识库名字、标题、内容是否正确！")
                return None, [one_title]
            docs = [Document(page_content=one_conent + "\n", metadata={"source": one_title})]
            if not one_content_segmentation:
                text_splitter = ChineseTextSplitter(pdf=False, sentence_size=sentence_size)
                docs = text_splitter.split_documents(docs)
            vector_store = add_vector_store(vs_path, self.embeddings, docs)
            return vs_path, [one_title]
        except Exception as e:
            logger.error(e)
            return None, [one_title]

    def one_knowledge_add_content(self, vs_path, content, metadata, sentence_size):
        try:
            if not vs_path or not content or metadata:
                logger.info("知识库添加错误，请确认知识库名字、标题、内容是否正确！")
                return None
            docs = [Document(page_content=content + "\n", metadata=metadata)]
            text_splitter = ChineseTextSplitter(pdf=False, sentence_size=sentence_size)
            docs = text_splitter.split_documents(docs)
            vector_store = add_vector_store(vs_path, self.embeddings, docs)
            return vs_path
        except Exception as e:
            logger.error(e)
            return None

    def question_generator(self, query, chat_history=[], prompt_template=CONDENSE_QUESTION_PROMPT, history_len=LLM_HISTORY_LEN):
        company_name = company(query, chat_history)
        if chat_history:
            pass
            # chat_history = chat_history[-history_len:]
            # buffer = ""
            # for i, (old_query, response) in enumerate(chat_history):
            #     if old_query is None:
            #         continue
            #     human = "Human: " + old_query
            #     ai = "Assistant: " + response
            #     buffer += "\n" + "\n".join([human, ai])
            # prompt = prompt_template.replace("{question}", query).replace("{chat_history}", buffer)
            # for answer_result in self.llm.generatorAnswer(prompt):
            #     pass
            # resp = answer_result.llm_output["answer"]
            # print(f"question prompt {prompt}")
            # print(f"question answer {query} =====> {resp}")
            # return resp
        if company_name not in query:
            return company_name + query, company_name
        return query, company_name

    def question_generator_keywords(self, query, chat_history=[]):
        resp, company_name = self.question_generator(query, chat_history, prompt_template=CONDENSE_QUESTION_PROMPT_KEYWORDS, history_len=LLM_HISTORY_LEN)
        question, keywords = extract_question_and_keywords(resp)
        if question or keywords:
            print(f"extract question:{question} keywords:{keywords}")
            return question, keywords, company_name
        print(f"resp: {resp}")
        return resp, resp, company_name

    def get_knowledge_based_answer(self, query, vs_path, chat_history=[], streaming: bool = STREAMING):
        question, keywords, company_name = self.question_generator_keywords(query, chat_history)
        if company_name != "":
            new_vs_path = vs_path + "_" + COMPANY_CODES[company_name]
            if has_vector_store(new_vs_path):
                vs_path = new_vs_path
        if not has_vector_store(vs_path):
            response = {"query": query,
                        "result": "知识库不存在, 请联系技术支持人员",
                        "source_documents": []}
            return response, chat_history
        print("collection name", vs_path)

        s = time.perf_counter()
        vector_store = load_vector_store(vs_path, self.embeddings)
        vector_store.chunk_size = self.chunk_size
        vector_store.chunk_conent = self.chunk_conent
        vector_store.score_threshold = self.score_threshold
        related_docs_with_score = vector_store.similarity_search_with_score(keywords, k=self.top_k)
        elapsed = time.perf_counter() - s
        print(f"知识库搜索 结束{elapsed:0.2f} seconds len:{len(related_docs_with_score)}")
        torch_gc()
        if streaming:
            response = {"query": query,
                        "result": "",
                        "source_documents": related_docs_with_score
                        }
            yield response, chat_history
        if len(related_docs_with_score) > 0:
            prompt = generate_prompt(related_docs_with_score, question)
        else:
            prompt = question

        for answer_result in self.llm.generatorAnswer(prompt=prompt, history=chat_history,
                                                      streaming=streaming):
            resp = answer_result.llm_output["answer"]
            history = answer_result.history
            history[-1][0] = query
            response = {"query": query,
                        "result": resp,
                        "source_documents": related_docs_with_score}
            yield response, history

    # query      查询内容
    # vs_path    知识库路径
    # chunk_conent   是否启用上下文关联
    # score_threshold    搜索匹配score阈值
    # vector_search_top_k   搜索知识库内容条数，默认搜索5条结果
    # chunk_sizes    匹配单段内容的连接上下文长度
    def get_knowledge_based_conent_test(self, query, vs_path, chunk_conent,
                                        score_threshold=VECTOR_SEARCH_SCORE_THRESHOLD,
                                        vector_search_top_k=VECTOR_SEARCH_TOP_K, chunk_size=CHUNK_SIZE):
        vector_store = load_vector_store(vs_path, self.embeddings)
        # FAISS.similarity_search_with_score_by_vector = similarity_search_with_score_by_vector
        # Milvus.similarity_search_with_score_by_vector = similarity_search_with_score_by_vector
        vector_store.chunk_conent = chunk_conent
        vector_store.score_threshold = score_threshold
        vector_store.chunk_size = chunk_size
        related_docs_with_score = vector_store.similarity_search_with_score(query, k=vector_search_top_k)
        if not related_docs_with_score:
            response = {"query": query,
                        "source_documents": []}
            return response, ""
        torch_gc()
        prompt = "\n".join([doc.page_content for doc in related_docs_with_score])
        response = {"query": query,
                    "source_documents": related_docs_with_score}
        return response, prompt

    def get_search_result_based_answer(self, query, chat_history=[], streaming: bool = STREAMING):
        question, keywords = self.question_generator_keywords(query, chat_history)
        results = bing_search(keywords)
        result_docs = search_result2docs(results)
        if streaming:
            response = {"query": query,
                        "result": "",
                        "source_documents": result_docs
                        }
            yield response, chat_history
        prompt = generate_prompt(result_docs, question)

        for answer_result in self.llm.generatorAnswer(prompt=prompt, history=chat_history,
                                                      streaming=streaming):
            resp = answer_result.llm_output["answer"]
            history = answer_result.history
            history[-1][0] = query
            response = {"query": query,
                        "result": resp,
                        "source_documents": result_docs}
            yield response, history

    def get_knowledge_union_google_search_based_answer(self, query, vs_path, chat_history=[],
                                                       streaming: bool = STREAMING, knowledge_ratio: float = 0.5):
        """
            描述：获取知识库和google搜索的内容集合
            knowledge_ratio：知识库占比（0-1）
        """
        question, keywords, company_name = self.question_generator_keywords(query, chat_history)
        if company_name != "":
            new_vs_path = vs_path + "_" + COMPANY_CODES[company_name]
            if has_vector_store(new_vs_path):
                vs_path = new_vs_path
        if not has_vector_store(vs_path):
            response = {"query": query,
                        "result": "知识库不存在, 请联系技术支持人员",
                        "source_documents": []}
            return response, chat_history
        print("collection name", vs_path)
        s = time.perf_counter()
        # 谷歌搜索
        results = google_search(keywords, self.top_k)
        gdocs = search_result2docs(results)
        elapsed = time.perf_counter() - s
        print(f"google搜索 结束 {elapsed:0.2f} seconds len:{len(gdocs)}")
        # 知识库搜索
        vector_store2 = load_vector_store(vs_path, self.embeddings)
        vector_store2.chunk_size = self.chunk_size
        vector_store2.chunk_conent = self.chunk_conent
        vector_store2.score_threshold = self.score_threshold
        related_docs_with_score = vector_store2.similarity_search_with_score(keywords, self.top_k)
        ldocs = [doc for doc in related_docs_with_score]
        elapsed = time.perf_counter() - s
        print(f"知识库搜索 结束{elapsed:0.2f} seconds len:{len(ldocs)}")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=SENTENCE_SIZE, chunk_overlap=0)
        docs = text_splitter.split_documents(gdocs+ldocs)
        vector_store = MyFAISS.from_documents(docs, self.embeddings)
        vector_store.chunk_size = self.chunk_size
        vector_store.chunk_conent = self.chunk_conent
        vector_store.score_threshold = self.score_threshold
        elapsed = time.perf_counter() - s
        print(f"本地向量化 {elapsed:0.2f} seconds len:{len(docs)}")
        result_docs = vector_store.similarity_search_with_score(query, self.top_k)
        torch_gc()
        elapsed = time.perf_counter() - s
        print(f"本地向量化搜索 结束 {elapsed:0.2f} seconds len:{len(result_docs)}")

        if result_docs is None or len(result_docs) == 0:
            response = {"query": query,
                        "result": "无法找到相关知识",
                        "source_documents": []}
            return response, chat_history

        if streaming:
            response = {"query": query,
                        "result": "",
                        "source_documents": result_docs
                        }
            yield response, chat_history

        # prompt = generate_prompt(result_docs, question)
        prompt = generate_few_shot_prompt(result_docs, question, self.embeddings)
        for answer_result in self.llm.generatorAnswer(prompt=prompt, history=chat_history,
                                                      streaming=streaming):
            resp = answer_result.llm_output["answer"]
            history = answer_result.history
            history[-1][0] = query
            response = {"query": query,
                        "result": resp,
                        "source_documents": result_docs}
            yield response, history
        elapsed = time.perf_counter() - s
        print(f"AI结束 {elapsed:0.2f} seconds")

    def get_search_result_google_answer(self, query, chat_history=[], streaming: bool = STREAMING):
        question, keywords = self.question_generator_keywords(query, chat_history)
        s = time.perf_counter()
        results = google_search(keywords, self.top_k)
        gdocs = search_result2docs(results)
        elapsed = time.perf_counter() - s
        print(f"google搜索 结束 {elapsed:0.2f} seconds len:{len(gdocs)}")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=SENTENCE_SIZE, chunk_overlap=0)
        docs = text_splitter.split_documents(gdocs)
        vector_store = MyFAISS.from_documents(docs, self.embeddings)
        vector_store.chunk_size = self.chunk_size
        vector_store.chunk_conent = self.chunk_conent
        vector_store.score_threshold = self.score_threshold
        elapsed = time.perf_counter() - s
        print(f"本地向量化 {elapsed:0.2f} seconds len:{len(docs)}")

        result_docs = vector_store.similarity_search_with_score(keywords, self.top_k)
        torch_gc()
        elapsed = time.perf_counter() - s
        print(f"本地向量化搜索 结束 {elapsed:0.2f} seconds len:{len(result_docs)}")

        if streaming:
            response = {"query": query,
                        "result": "",
                        "source_documents": result_docs
                        }
            yield response, chat_history

        if result_docs is None or len(result_docs) == 0:
            response = {"query": query,
                        "result": "无法找到相关知识",
                        "source_documents": result_docs}
            yield response, chat_history
            return

        # prompt = generate_prompt(result_docs, question)
        prompt = generate_few_shot_prompt(result_docs, question, self.embeddings)
        for answer_result in self.llm.generatorAnswer(prompt=prompt, history=chat_history,
                                                      streaming=streaming):
            resp = answer_result.llm_output["answer"]
            history = answer_result.history
            history[-1][0] = query
            response = {"query": query,
                        "result": resp,
                        "source_documents": result_docs}
            yield response, history
        elapsed = time.perf_counter() - s
        print(f"AI结束 {elapsed:0.2f} seconds")

    def delete_file_from_vector_store(self,
                                      filepath: str or List[str],
                                      vs_path):
        vector_store = load_vector_store(vs_path, self.embeddings)
        status = vector_store.delete_doc(filepath)
        return status

    def update_file_from_vector_store(self,
                                      filepath: str or List[str],
                                      vs_path,
                                      docs: List[Document], ):
        vector_store = load_vector_store(vs_path, self.embeddings)
        status = vector_store.update_doc(filepath, docs)
        return status

    def list_file_from_vector_store(self,
                                    vs_path,
                                    fullpath=False):
        vector_store = load_vector_store(vs_path, self.embeddings)
        docs = vector_store.list_docs()
        if fullpath:
            return docs
        else:
            return [os.path.split(doc)[-1] for doc in docs]


if __name__ == "__main__":
    # 初始化消息
    args = None
    args = parser.parse_args(args=['--model-dir', '/media/checkpoint/', '--model', 'chatglm-6b', '--no-remote-model'])

    args_dict = vars(args)
    shared.loaderCheckPoint = LoaderCheckPoint(args_dict)
    llm_model_ins = shared.loaderLLM()
    llm_model_ins.set_history_len(LLM_HISTORY_LEN)

    local_doc_qa = LocalDocQA()
    local_doc_qa.init_cfg(llm_model=llm_model_ins)
    query = "本项目使用的embedding模型是什么，消耗多少显存"
    vs_path = "/media/gpt4-pdf-chatbot-langchain/dev-aifin/vector_store/test"
    last_print_len = 0
    # for resp, history in local_doc_qa.get_knowledge_based_answer(query=query,
    #                                                              vs_path=vs_path,
    #                                                              chat_history=[],
    #                                                              streaming=True):
    for resp, history in local_doc_qa.get_search_result_based_answer(query=query,
                                                                     chat_history=[],
                                                                     streaming=True):
        print(resp["result"][last_print_len:], end="", flush=True)
        last_print_len = len(resp["result"])
    source_text = [f"""出处 [{inum + 1}] {doc.metadata['source'] if doc.metadata['source'].startswith("http")
    else os.path.split(doc.metadata['source'])[-1]}：\n\n{doc.page_content}\n\n"""
                   # f"""相关度：{doc.metadata['score']}\n\n"""
                   for inum, doc in
                   enumerate(resp["source_documents"])]
    logger.info("\n\n" + "\n\n".join(source_text))
    pass
