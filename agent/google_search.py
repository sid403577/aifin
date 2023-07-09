import urllib.parse
from typing import List, Dict

import chardet
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from models.base import BaseAnswer
from configs.model_config import GOOGLE_API_KEY, GOOGLE_CSE_ID, PROMPT_TEMPLATE

#my_api_key = "AIzaSyACpSZ6gtDOKFadgM651TNu7DdzvtStX6Y"
#my_cse_id = "d4451a0622ff94fc7"

htmlcontent = {
    "www.prnasia.com": {
        "element": "div",
        "attr": {'id': 'dvContent'},
        "name": "美通社",
        "enable": True,
        "sort": 1,

    },
    "finance.stockstar.com": {
        "element": "div",
        "attr": {'class': 'article_content'},
        "testCaseList": ['https://finance.stockstar.com/IG2022032400001037.shtml'],
        "name": "证券之星",
        "enable": True,
        "sort": 2,
    },
    "business.sohu.com": {
        "element": "article",
        "attr": {'class': 'article-text'},
        "testCaseList": ['https://business.sohu.com/a/642076928_114984?scm=1103.plate:611:0.0.1_1.0'],
        "name": "搜狐财经",
        "enable": True,
        "sort": 3,
    },
    "finance.sina.com.cn": {
        "element": "div",
        "attr": {"class": "article"},
        "testCaseList": ['https://finance.sina.com.cn/money/fund/jjzl/2023-06-15/doc-imyxknym3210622.shtml'],
        "name": "新浪财经",
        "enable": True,
        "sort": 4,
    },
    "libattery.ofweek.com": {
        "element": "div",
        "attr": {"class": "artical-content"},
        "testCaseList": ['https://libattery.ofweek.com/2022-06/ART-36002-8420-30566059.html'],
        "name": "维科网",
        "enable": True,
        "sort": 5,
    },
    "origin-view.inews.qq.com": {
        "element": "div",
        "attr": {"id": "ArticleContent"},
        "testCaseList": ['https://origin-view.inews.qq.com/a/20230615A05WAP00?%23=&uid='],
        "name": "腾讯新闻子网",
        "enable": True,
        "sort": 6,
    },
    "finance.ce.cn": {
        "element": "div",
        "attr": {"class": "content"},
        "testCaseList": ['http://finance.ce.cn/stock/gsgdbd/202207/09/t20220709_37849475.shtml'],
        "name": "中国经济网",
        "enable": True,
        "sort": 7,
    },
    "cn.nytimes.com": {
        "element": "section",
        "attr": {"class": "article-body"},
        "testCaseList": ['https://cn.nytimes.com/business/20211222/china-catl-electric-car-batteries/'],
        "name": "纽约时报中文网",
        "enable": True,
        "sort": 8,
    },
    "www.reuters.com": {
        "element": "div",
        "attr": {"class": "ArticleBodyWrapper"},
        "testCaseList": ['https://www.reuters.com/article/amperex-germany-ev-battery-plant-0709-mo-idCNKBS1K005E'],
        "name": "路透社网站",
        "enable": True,
        "sort": 9,
    }
}


def _google_search(search_term, api_key, cse_id, **kwargs) -> List[Dict]:
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    return res['items']


def google_search(text, result_len=10,llm: BaseAnswer = None):
    print("google_search开始")
    results = _google_search(text, GOOGLE_API_KEY, GOOGLE_CSE_ID, num=result_len)
    print(f"results:{results}")
    metadata_results = []
    if len(results) == 0:
        return [{"Result": "No good Google Search Result was found"}]
    for result in results:
        metadata_result = {
            "title": result["title"],
            "link": result["link"],
        }

        content = get_text(result["link"], result["displayLink"])
        if content:
            print("调用llm模型获取摘要数据---------")
            prompt = PROMPT_TEMPLATE.replace("{question}", text).replace("{context}", content)
            answer_result = llm.generatorAnswer(prompt=prompt, history=[],streaming=False)
            resp = answer_result.llm_output["answer"]
            metadata_result["snippet"] = resp
        elif "snippet" in result:
            metadata_result["snippet"] = result["snippet"]

        metadata_results.append(metadata_result)
    print("google_search结束")
    return metadata_results


def get_text(link: str, displayLink: str):
    try:
        if displayLink in htmlcontent:
            params = htmlcontent[displayLink]
            if 'enable' in params and params['enable']:
                text = download_page(url=link)
                if text:
                    soup = BeautifulSoup(text)
                    return soup.find_all(params['element'], params['attr'])[0].get_text()
    except Exception as e:
        print(f"error:获取内容异常，link：{link},异常信息：{e}")


def download_page(url, para=None):
    normalUrl = "https://api.crawlbase.com/?token=gRg5wZGhA4tZby6Ihq_6IQ&url="
    crawUrl = f"{normalUrl}{urllib.parse.quote(url)}"
    if para:
        response = requests.get(url, params=para)
    else:
        response = requests.get(url)
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


if __name__ == '__main__':
    text = google_search("宁德时代")
    print(text)
