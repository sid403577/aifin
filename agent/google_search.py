

import os
#my_api_key = "AIzaSyAQwvxsjirV3fXxQ_oCClvg5wct0Vyzq8A"
#my_cse_id = "a641dd528fa274bc3"
os.environ["GOOGLE_CSE_ID"] = "a641dd528fa274bc3"
os.environ["GOOGLE_API_KEY"] = "AIzaSyAQwvxsjirV3fXxQ_oCClvg5wct0Vyzq8A"

from langchain.tools import Tool
from langchain.utilities import GoogleSearchAPIWrapper

search = GoogleSearchAPIWrapper()

def google_search(text, result_len=10):
    def top5_results(query):
        return search.results(query, result_len)
    tool = Tool(
        name="Google Search Snippets",
        description="Search Google for recent results.",
        func=top5_results,
    )
    return tool.run(text)

if __name__ == "__main__":
    r = google_search('python')
    print(r)