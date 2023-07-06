#coding=utf8

import os
from configs.model_config import GOOGLE_API_KEY, GOOGLE_CSE_ID

from langchain.utilities import GoogleSearchAPIWrapper
def google_search(text, result_len=3):
    if not (GOOGLE_API_KEY and GOOGLE_CSE_ID):
        return [{"snippet": "please set GOOGLE_API_KEY and GOOGLE_CSE_ID in os ENV",
                 "title": "env info is not found",
                 "link": "https://python.langchain.com/en/latest/modules/agents/tools/examples/google_search.html"}]
    search = GoogleSearchAPIWrapper(google_api_key=GOOGLE_API_KEY,
                                  google_cse_id=GOOGLE_CSE_ID)
    return search.results(text, result_len)

if __name__ == "__main__":
    r = google_search('python')
    print(r)