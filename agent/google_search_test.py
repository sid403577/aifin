from typing import List, Dict

from googleapiclient.discovery import build

#my_api_key = "AIbaSyAEY6egFSPeadgK7oS/54iQ_ejl24s4Ggc" #The API_KEY you acquired
#my_cse_id = "012345678910111213141:abcdef10g2h" #The search-engine-ID you created
my_api_key = "AIzaSyAQwvxsjirV3fXxQ_oCClvg5wct0Vyzq8A"
my_cse_id = "a641dd528fa274bc3"


def _google_search(search_term, api_key, cse_id, **kwargs)-> List[Dict]:
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    return res['items']

def google_search(text, result_len=3):
    results = _google_search(text, my_api_key, my_cse_id, result_len)
    metadata_results = []
    if len(results) == 0:
        return [{"Result": "No good Google Search Result was found"}]
    for result in results:
        metadata_result = {
            "title": result["title"],
            "link": result["link"],
        }
        if "snippet" in result:
            metadata_result["snippet"] = result["snippet"]

        metadata_results.append(metadata_result)


    return metadata_results


