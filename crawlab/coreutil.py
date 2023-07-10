
###################### 获取数据 ###############################################

import datetime
import json
import re
import sys
import urllib.parse

import chardet
import requests
from bs4 import BeautifulSoup

normalUrl = "https://api.crawlbase.com/?token=mjBM5V0p5xIDxV1N9MqYpg"

htmlcontent={
    "search-api-web.eastmoney.com":{
        "domainurl":"https://search-api-web.eastmoney.com/search/jsonp?cb=jQuery35107761762966427765_1687662386467",
        "parse_param":{
            "key":"param",
            "value":'{"uid": "4529014368817886", "keyword": "$code", "type": ["cmsArticleWebOld"], "client": "web", "clientType": "web", "clientVersion": "curr", "param": {"cmsArticleWebOld": {"searchScope": "default", "sort": "time", "pageIndex": $pageIndex, "pageSize": $pageSize, "preTag": "<em>", "postTag": "</em>"}}}',
        },
        "result_re":'jQuery35107761762966427765_1687662386467\((.*)\)',
        "data":['result','cmsArticleWebOld'],
        "text_re":{
            "element": "div",
            "attr": {"class": "article"},
        }


    }
}

def download_page(url, para=None):
    crawUrl = f"{normalUrl}&url={urllib.parse.quote(url)}"
    if para:
        response = requests.get(crawUrl, params=para)
    else:
        response = requests.get(crawUrl)
    # response.encoding = response.apparent_encoding
    if response.status_code == 200:
        # 以下为乱码异常处理
        try:
            code1 = chardet.detect(response.content)['encoding']
            text = response.content.decode(code1)
        except:
            code = response.encoding
            try:
                text = response.text.encode(code).decode('utf-8')
            except:
                try:
                    text = response.text.encode(code).decode('gbk')
                except:
                    text = response.text
        return text
    else:
        print("failed to download the page")


def eastmoney(domain:str,code: str, type: str, startPage=1):  # 两个参数分别表示开始读取与结束读取的页码

    param_content = htmlcontent[domain]
    if not param_content:
        print(f"该域名数据无法获取，domain:{domain}")
        return


    # 遍历每一个URL
    total = 0
    pageIndex = startPage
    pageSize = 10
    flag = True

    while flag:
        print(f"开始获取第{pageIndex}页数据")

        domainurl:str = param_content['domainurl']
        domainurl = domainurl.replace("$code",code).replace("$pageIndex",str(pageIndex)).replace("$pageSize",str(pageSize))
        parse_param = param_content['parse_param']
        link = f"{domainurl}"
        if parse_param:
            key = parse_param['key']
            value:str = parse_param['value']
            value = value.replace("$code",code).replace("$pageIndex",str(pageIndex)).replace("$pageSize",str(pageSize))
            link = link+"&"+key+"="+urllib.parse.quote(value)

        print(f"link:{link}")  # 用于检查
        crawUrl = f"{normalUrl}&url={urllib.parse.quote(link)}"
        response = requests.get(crawUrl, verify=False, timeout=30)  # 禁止重定向
        print(response.text)
        content = response.text
        if 'result_re' in param_content:
            content = re.findall(param_content['result_re'], response.text)[0]
        # 读取的是json文件。因此就用json打开啦
        data = json.loads(content)
        # 找到原始页面中数据所在地
        for pre in param_content['data']:
            data = data[pre]

        print(f"获取第{pageIndex}页的数据，大小为{len(data)}")
        storageList: list[Document] = []
        for i in range(0, len(data)):

            try:
                date = data[i]['date']
                if type == "1":
                    s_date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').date()
                    Yesterday = datetime.date.today()-datetime.timedelta(days=1)
                    if s_date == Yesterday:
                        print(f"昨天的数据已经处理完成，跳出循环")
                        flag = False
                        break

                total += 1
                print(f"开始处理第{total}条数据：{data[i]}")
                # 数据处理
                print(f"获取第{total}条数据的link内容：{link}")
                text = get_text(data[i]['url'],param_content['text_re'])
                url = data[i]['url']
                title = data[i]['title']
                createTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if text:
                    text = text.replace('</em>', '').replace('<em>', '')
                if title:
                    title = title.replace('</em>', '').replace('<em>', '')
                # 写入
                doc = Document(page_content=text,
                               metadata={"source": "Web",
                                         "code": code,
                                         "url": url,
                                         "date": date,
                                         "type": "资讯",
                                         "from": "eastmoney.com",
                                         "createTime": createTime,
                                         "title": title})
                storageList.append(doc)

                print(f"第{total}条数据处理完成")

            except Exception as e:
                print(f"获取第【{pageIndex}】页的第【{i}】条数据,title:{data[i]['title']},url:{data[i]['url']}时异常，异常信息：{e}")
        # 存入矢量库
        if len(storageList) > 0:
            store(storageList)

        print(f"第{pageIndex}页数据处理完成")
        if len(data) < pageSize:
            break
        pageIndex += 1

    print(f"处理完成，从{startPage}-{pageIndex}页，一共处理{total}条数据")


def get_text(url,text_re:dict):
    soup = BeautifulSoup(download_page(url))
    all_comments = soup.find_all(text_re['element'], text_re['attr'])
    if all_comments and len(all_comments) > 0:
        text1 = all_comments[0]
        con = text1.get_text()  # 只提取文字
    else:
        con = soup.get_text()
    return con


###################### 存储类 ###############################################

from typing import List

import torch
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Milvus
from langchain.text_splitter import CharacterTextSplitter

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
    docs = []
    content = "近日，网传今年2月份抢教授话筒的蒋同学高考655分，被哈工大录取。对此，7月6日，哈尔滨工业大学招生办工作人员回应称，录取还没开始，各省尚未投档，投档结束了才知道，录取时间可能在20日左右。"
    source = "https://mbd.baidu.com/newspage/data/landingsuper?context=%7B%22nid%22%3A%22news_9605400130597382296%22%7D&n_type=-1&p_from=-1"
    doc = Document(page_content=content,
                   metadata={"source": source,
                             "date": "2022-09-10 12:20:20",
                             "title": "高考"})
    docs.append(doc)
    return docs


def load_and_split(docs: list[Document],sentence_size=100) -> list[Document]:
    """Load documents and split into chunks."""
    _text_splitter = ChineseTextSplitter(pdf=False, sentence_size=sentence_size)
    return _text_splitter.split_documents(docs)


def store(docs: list[Document]):
    docs = load_and_split(docs)
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model_dict[EMBEDDING_MODEL],
                                       model_kwargs={'device': EMBEDDING_DEVICE})
    vector_db = Milvus.from_documents(
        docs,
        embeddings,
        connection_args={"host": "8.217.52.63", "port": "19530"},
    )
    docs = vector_db.similarity_search("蒋同学高考")
    if docs and len(docs) > 0:
        content = [doc.page_content for doc in docs]
        print(content)
    print("over")


###################### 分词类 ###############################################

from langchain.text_splitter import CharacterTextSplitter
import re
from typing import List

class ChineseTextSplitter(CharacterTextSplitter):
    def __init__(self, pdf: bool = False, sentence_size: int = 100, **kwargs):
        super().__init__(**kwargs)
        self.pdf = pdf
        self.sentence_size = sentence_size

    def split_text1(self, text: str) -> List[str]:
        if self.pdf:
            text = re.sub(r"\n{3,}", "\n", text)
            text = re.sub('\s', ' ', text)
            text = text.replace("\n\n", "")
        sent_sep_pattern = re.compile('([﹒﹔﹖﹗．。！？]["’”」』]{0,2}|(?=["‘“「『]{1,2}|$))')  # del ：；
        sent_list = []
        for ele in sent_sep_pattern.split(text):
            if sent_sep_pattern.match(ele) and sent_list:
                sent_list[-1] += ele
            elif ele:
                sent_list.append(ele)
        return sent_list

    def split_text(self, text: str) -> List[str]:   ##此处需要进一步优化逻辑
        if self.pdf:
            text = re.sub(r"\n{3,}", r"\n", text)
            text = re.sub('\s', " ", text)
            text = re.sub("\n\n", "", text)

        text = re.sub(r'([;；.!?。！？\?])([^”’])', r"\1\n\2", text)  # 单字符断句符
        text = re.sub(r'(\.{6})([^"’”」』])', r"\1\n\2", text)  # 英文省略号
        text = re.sub(r'(\…{2})([^"’”」』])', r"\1\n\2", text)  # 中文省略号
        text = re.sub(r'([;；!?。！？\?]["’”」』]{0,2})([^;；!?，。！？\?])', r'\1\n\2', text)
        # 如果双引号前有终止符，那么双引号才是句子的终点，把分句符\n放到双引号后，注意前面的几句都小心保留了双引号
        text = text.rstrip()  # 段尾如果有多余的\n就去掉它
        # 很多规则中会考虑分号;，但是这里我把它忽略不计，破折号、英文双引号等同样忽略，需要的再做些简单调整即可。
        ls = [i for i in text.split("\n") if i]
        for ele in ls:
            if len(ele) > self.sentence_size:
                ele1 = re.sub(r'([,，.]["’”」』]{0,2})([^,，.])', r'\1\n\2', ele)
                ele1_ls = ele1.split("\n")
                for ele_ele1 in ele1_ls:
                    if len(ele_ele1) > self.sentence_size:
                        ele_ele2 = re.sub(r'([\n]{1,}| {2,}["’”」』]{0,2})([^\s])', r'\1\n\2', ele_ele1)
                        ele2_ls = ele_ele2.split("\n")
                        for ele_ele2 in ele2_ls:
                            if len(ele_ele2) > self.sentence_size:
                                ele_ele3 = re.sub('( ["’”」』]{0,2})([^ ])', r'\1\n\2', ele_ele2)
                                ele2_id = ele2_ls.index(ele_ele2)
                                ele2_ls = ele2_ls[:ele2_id] + [i for i in ele_ele3.split("\n") if i] + ele2_ls[
                                                                                                       ele2_id + 1:]
                        ele_id = ele1_ls.index(ele_ele1)
                        ele1_ls = ele1_ls[:ele_id] + [i for i in ele2_ls if i] + ele1_ls[ele_id + 1:]

                id = ls.index(ele)
                ls = ls[:id] + [i for i in ele1_ls if i] + ls[id + 1:]
        return ls


if __name__ == "__main__":
    # code = input('请输入股票代码：')
    # Start = input('请输入起始页：')
    # size = input('请输入每页大小：')
    # End = input('请输入结束页：')
    domain = sys.argv[1]  # 域名
    code = sys.argv[2]  # 股票代码
    type = sys.argv[3]  # 增量1，全量2
    startPage = sys.argv[4]  # 从第几页
    print(f"参数列表，domain:{domain},code:{code},type:{type},startPage:{startPage}")
    eastmoney(domain,code, type, int(startPage))
    # output_csv(result)
