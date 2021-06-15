#python3
import urllib.request
import urllib.parse
import json
import time
import base64
from engine.predictor import predictor

headers = {
        'Authorization': 'YOUR KEY', # <-- Manual Edit 1.
        'Content-Type': 'application/json; charset=UTF-8'
        }

def posturl(url,data):
    try:
        params=json.dumps(data).encode(encoding='UTF8')
        req = urllib.request.Request(url, params, headers)
        r = urllib.request.urlopen(req)
        html =r.read()
        r.close();
        return html.decode("utf8")
    except urllib.error.HTTPError as e:
        print(e.code)
        print(e.read().decode("utf8"))

def fetch_text(b64_image):
    url_request="https://tysbgpu.market.alicloudapi.com/api/predict/ocr_general" # <-- Manual Edit 2, Change to your API provider.
    post_dict = {'image': b64_image}
    html = posturl(url_request, data=post_dict)
    if not html == None:
        json_from_result = json.loads(html)
    else:
        return None
    return json_from_result

def b64_to_text_list(b64_image):
    result = fetch_text(b64_image)
    if result == None:
        return []

    all_words = []
    try: # some might lack "ret"
        for item in result['ret']:  # <-- Manual Edit 3, fetch all words from your OCR result. This could differ greately between providers.
            try: # some might lack "word"
                word = item['word']
                all_words.append(word)
            except:
                pass
    except:
        pass

    joined_string = ' '.join(all_words)
    cut_list = predictor.cut(joined_string)
    cleaned_list = list(filter(lambda a: a != ' ', list(cut_list) )) # remove all spaces
    return cleaned_list

