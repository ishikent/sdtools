from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from collections import OrderedDict
import os
import pathlib
import json
import argparse

from bs4 import BeautifulSoup
import asyncio

base_url = "https://danbooru.donmai.us"
search_tmp_url = f"{base_url}/posts/"
preview_link_cls = ".post-preview-link"

def initalize(savedir):
    if not savedir.exists():
        os.mkdir(savedir)

def get_tag_list(soup, clsname): #clsnameの例："artist"
    taglist = []
    ul_ele = soup.select(f"aside#sidebar > section#tag-list > div.tag-list > ul.{clsname}-tag-list > li[data-tag-name]") #return bs4.element.resultset
    for li_ele in ul_ele:
        taglist.append(li_ele["data-tag-name"])

    return taglist


def get_tag_all(soup):
    od = OrderedDict()
    tag_cls_list = ["artist", "copyright", "character", "general", "meta"]
    for tag_cls in tag_cls_list:
        od[tag_cls] = get_tag_list(soup, tag_cls)

    return od

def get_info(soup):
    od = OrderedDict()
    inf_list = soup.select("section#post-information > ul > li") #情報を上から順に辞書に追加する
    for inf in inf_list:
        inf_type = inf["id"].split("-")[-1]
        od[inf_type] = get_info_by_type(inf_type, inf)
    
    return od

def get_info_by_type(type, tag):
    try : 
        if type in {"id", "size", "rating", "status"}:
            return tag.get_text(strip = True).split(":")[-1].strip() if tag.get_text(strip = True) else ""
        elif type == "uploader":
            return tag.find("a")["data-user-id"]
        elif type == "date":
            return tag.find("time")["datetime"]
        elif type == "source":
            return tag.find("a")["href"]
        elif type == "score":
            return tag.find(class_ = "post-score").get_text(strip = True)
        elif type == "favorites":
            return tag.find(class_ = "post-favcount").get_text(strip = True)
    except Exception:
        return None

def download_img(driver, url, id):
    extensions = url.split(".")[-1]
    save_binary(driver, url, id + "." + extensions)

def get_loaded_end_id(dirpath):
    hoge = sorted([i for i in dirpath.iterdir()], key=lambda x: int(str(x.name).split(".")[0]))
    if hoge:
        return int(str(hoge[0].name).split(".")[0])
    else :
        return 1

def get_latest_id(driver):
    driver.get(search_tmp_url)
    ele = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, preview_link_cls))) 

    return int(ele.get_attribute("href").split("/")[-1])

async def asyn_write(filepath, data_bytes):
    with open(filepath, 'wb') as bin_out:
        bin_out.write(bytes(data_bytes))

#普通にURLをとってきてrequests.getで画像を取得するのが一般的だが、
#danbooruは動的ページ+ anti bot serviceなのでpythonからのリクエストでは403になる
#よってselenium上で画像を保存するために以下の関数を使用する
def save_binary(driver, url, filepath):
    js = """
    var getBinaryResourceText = function(url) {
        var req = new XMLHttpRequest();
        req.open('GET', url, false);
        req.overrideMimeType('text/plain; charset=x-user-defined');
        req.send(null);
        if (req.status != 200) return '';

        var filestream = req.responseText;
        var bytes = [];
        for (var i = 0; i < filestream.length; i++){
            bytes[i] = filestream.charCodeAt(i) & 0xff;
        }

        return bytes;
    }
    """
    js += "return getBinaryResourceText(\"{url}\");".format(url=url)

    data_bytes = driver.execute_script(js)
    asyncio.run(asyn_write(filepath, data_bytes))

async def save_dict_as_json(dict, filename):
    with open(filename + ".json", "w") as f:
        json.dump(dict, f, indent = 4)

def get_options():

    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-extensions")
    options.add_argument('--disable-gpu')  
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-desktop-notifications')
    options.add_argument("--disable-extensions")
    options.add_argument('--lang=ja')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--proxy-server="direct://"')
    options.add_argument('--proxy-bypass-list=*')    
    options.add_argument('--start-maximized')

    return options

def keisoku(driver):
    js = """
        var timing = window.performance.timing;
        var tmp = '';
        tmp += `TCP接続時間:    ${timing.connectEnd - timing.connectStart} :`
        tmp += `リクエスト時間: ${timing.responseStart - timing.requestStart} :`
        tmp += `レスポンス時間: ${timing.responseEnd - timing.responseStart} :`
        tmp += `DOMの構築時間:  ${timing.domComplete - timing.domLoading} :`

        return tmp;
    """
    return driver.execute_script(js)


if __name__ == "__main__":
    count = 1
    parser = argparse.ArgumentParser()
    parser.add_argument("save_dir", default = "./", nargs="?")
    parser.add_argument("--start", default = 0, required=False, type=int)
    parser.add_argument("--end", default = 100, required=False, type=int)
    args = parser.parse_args()


    print(f"start: {args.start} ---- end: {args.end}")

    savedir = pathlib.Path(args.save_dir)
    dirname = savedir / "danimg"
    dirname1 = savedir / "danmeta"
    initalize(savedir)
    initalize(dirname)
    initalize(dirname1)

    import undetected_chromedriver.v2 as uc
    from pyvirtualdisplay import Display
    display = Display(visible=0, size=(800, 600))
    display.start()

    driver = uc.Chrome(use_subprocess=True, options = get_options())

    loded_end_id = get_loaded_end_id(dirname1)

    latest_id = get_latest_id(driver)
    print(f"loaded_last id : {loded_end_id}")
    print(f"latest id : {latest_id}")
    
    for id in range(max(loded_end_id, args.start), min(args.end, latest_id) + 1):
        print(f"loop id : {id}")
        tmp_url = f"{search_tmp_url}/{id}"
        driver.get(tmp_url)

        print(keisoku(driver))

        # try :
        #     WebDriverWait(driver, 3).until(EC.all_of(
        #         EC.presence_of_element_located((By.CSS_SELECTOR, "aside#sidebar > section#tag-list > div.tag-list > ul > li")), #タグ
        #         EC.presence_of_element_located((By.CSS_SELECTOR, "aside#sidebar > section#post-information > ul > li#post-info-id")), #information
        #         EC.presence_of_element_located((By.CSS_SELECTOR, "div.sidebar-container > section#content > section.image-container > picture > source")) #画像
        #     ))
        # except Exception:
        #     print("not found")
        #     continue

        # #パースhtmlを取得
        # html = driver.page_source.encode('utf-8')
        # soup = BeautifulSoup(html, "lxml")

        # # #画像保存
        # img_src = soup.select_one("div.sidebar-container > section#content > section.image-container > picture > source")["srcset"]
        # download_img(driver, img_src, f"{dirname}/{id:015}")

        # #メタ情報保存
        # od = OrderedDict()
        # od["tags"]         = get_tag_all(soup)
        # od["informations"] = get_info(soup)
        # asyncio.run(save_dict_as_json(od, f"{dirname1}/{id:015}"))

    driver.quit()
    display.stop()

