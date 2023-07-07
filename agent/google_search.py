from typing import List, Dict
import re

import chardet
from googleapiclient.discovery import build
import urllib.parse
import requests
from bs4 import BeautifulSoup
#my_api_key = "AIbaSyAEY6egFSPeadgK7oS/54iQ_ejl24s4Ggc" #The API_KEY you acquired
#my_cse_id = "012345678910111213141:abcdef10g2h" #The search-engine-ID you created
my_api_key = "AIzaSyAQwvxsjirV3fXxQ_oCClvg5wct0Vyzq8A"
my_cse_id = "a641dd528fa274bc3"



htmlcontent = {
    "www.prnasia.com":{
        "element":"div",
        "attr":{'id': 'dvContent'}
    },
    "finance.stockstar.com":{
        "element":"div",
        "attr":{'class': 'article_content'},
        "testCaseList":['https://finance.stockstar.com/IG2022032400001037.shtml']
    },
}

def _google_search(search_term, api_key, cse_id, **kwargs)-> List[Dict]:
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    return res['items']

def google_search(text, result_len=3):
    results = _google_search(text, my_api_key, my_cse_id, num=result_len)
    metadata_results = []
    if len(results) == 0:
        return [{"Result": "No good Google Search Result was found"}]
    for result in results:
        metadata_result = {
            "title": result["title"],
            "link": result["link"],
        }

        content = get_text(result["link"],result["displayLink"])
        if content:
            metadata_result["snippet"] = content
        elif "snippet" in result:
            metadata_result["snippet"] = result["snippet"]

        metadata_results.append(metadata_result)

    return metadata_results

def get_text(link:str,displayLink:str):
    try:
        if displayLink in htmlcontent:
            params = htmlcontent[displayLink]
            soup = BeautifulSoup(download_page(url=link))
            return soup.find_all(params['element'], params['attr'])[0].get_text()
    except Exception as e:
        print(f"error:获取内容异常，link：{link}"+e)
    return None
def download_page(url, para=None):
    normalUrl = "https://api.crawlbase.com/?token=gRg5wZGhA4tZby6Ihq_6IQ&url="
    crawUrl = f"{normalUrl}{urllib.parse.quote(url)}"
    if para:
        response = requests.get(url, params=para)
    else:
        response = requests.get(url)
    if response.status_code == 200:
        code1 = chardet.detect(response.content)['encoding']
        print(f"encoding:{code1}")
        text = response.content.decode(code1)
        # code = response.encoding
        #text = response.text
        # try:
        #     text = text.encode(code).decode('utf-8')
        # except:
        #     try:
        #         text = text.encode(code).decode('gbk')
        #     except:
        #         text = text
        return text
    else:
        print("failed to download the page")


if __name__ == '__main__':
    text= google_search("宁德时代的股价")
    print(text)

