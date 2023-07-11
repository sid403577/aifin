import chardet
import requests
from bs4 import BeautifulSoup
import re

def download_page(url, para=None):
    #normalUrl = "https://api.crawlbase.com/?token=gRg5wZGhA4tZby6Ihq_6IQ&url="
    #crawUrl = f"{normalUrl}{urllib.parse.quote(url)}"
    if para:
        response = requests.get(url, params=para)
    else:
        response = requests.get(url)
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
    else:
        print("failed to download the page")
    return text

if __name__ == '__main__':
    domainurl = "http://www.baidu.com/s?ie=utf-8&medium=0&rtt=1&bsst=1&rsv_dl=news_t_sk&cl=2&wd=%E5%AE%8C%E7%BE%8E%E4%B8%96%E7%95%8C&tn=news&rsv_bp=1&rsv_sug3=1&rsv_sug1=1&rsv_sug7=100&rsv_sug2=0&oq=&rsv_btype=t&f=8&inputT=3&rsv_sug4=697"
    url2 = "https://www.reuters.com/article/amperex-germany-ev-battery-plant-0709-mo-idCNKBS1K005E"
    print(url2)  # 用于检查
    text = download_page(url2)
    print(f"text:{text}")
    soup = BeautifulSoup(text)
    all_comments = soup.find_all("div", {'class': 'article_content'})[0].get_text()
    print(all_comments)



