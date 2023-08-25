import chardet
import requests
from bs4 import BeautifulSoup
import urllib.parse
def get_text(url, text_re: dict):
    soup = BeautifulSoup(download_page(url))
    all_comments = soup.find_all(text_re['element'], text_re['attr'])
    if all_comments and len(all_comments) > 0:
        text1 = all_comments[0]
        con = text1.get_text()  # 只提取文字
    else:
        con = soup.get_text()
    return con
def download_page(url:str, para=None):
    if not url or len(url.strip())==0:
        return ""

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
    pagesis = {
        "element": "div",
        # "attr": {"class": "article"},
        "attr": {"class": "newsContent"},
    }
    text = get_text("https://data.eastmoney.com/report/info/AP202308251595831947.html",pagesis)
    print(text)
