from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from collections import OrderedDict
import os
import pathlib
import json
import argparse
import time

base_url = "https://danbooru.donmai.us"
search_tmp_url = f"{base_url}/posts/"
preview_link_cls = ".post-preview-link"

def initalize(savedir):
    if not savedir.exists():
        os.mkdir(savedir)


def get_imgsrc(driver):
    try :
        imgele = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "img#image"))) 
        return imgele.get_attribute("src")
    except :
        return None


def get_tag_list(driver, clsname): #clsnameの例："artist"
    taglist = []
    ul_ele = driver.find_elements(By.CSS_SELECTOR, f"ul.{clsname}-tag-list > li[data-tag-name]")
    for li_ele in ul_ele:
        taglist.append(li_ele.get_attribute("data-tag-name"))

    return taglist


def get_tag_all(driver):
    od = OrderedDict()
    tag_cls_list = ["artist", "copyright", "character", "general", "meta"]
    for tag_cls in tag_cls_list:
        od[tag_cls] = get_tag_list(driver, tag_cls)

    return od

def get_info(driver):
    od = OrderedDict()
    inf_list = driver.find_elements(By.CSS_SELECTOR, "section#post-information > ul > li") #情報を上から順に辞書に追加する
    for inf in inf_list:
        inf_type = inf.get_attribute("id").split("-")[-1]
        od[inf_type] = get_info_by_type(driver, inf_type, inf)
    
    return od

def get_info_by_type(driver, type, element):
    try : 
        if type in {"id", "size", "rating", "status"}:
            return element.text.split(":")[-1].strip() if element.text else ""
        elif type == "uploader":
            user_id = element.find_element(By.TAG_NAME, "a").get_attribute("data-user-id")
            return user_id
        elif type == "date":
            return element.find_element(By.TAG_NAME, "time").get_attribute("datetime")
        elif type == "source":
            return element.find_element(By.TAG_NAME, "a").get_attribute("href")
        elif type == "score":
            return element.find_element(By.CLASS_NAME, "post-score").text
        elif type == "favorites":
            return element.find_element(By.CLASS_NAME, "post-favcount").text
    except Exception:
        return None

def download_img(url, id):
    extensions = url.split(".")[-1]
    save_binary(url, id + "." + extensions)

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


#普通にURLをとってきてrequests.getで画像を取得するのが一般的だが、
#danbooruは動的ページ+ anti bot serviceなのでpythonからのリクエストでは403になる
#よってselenium上で画像を保存するために以下の関数を使用する
def save_binary(url, filepath):
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
    with open(filepath, 'wb') as bin_out:
        bin_out.write(bytes(data_bytes))

def save_dict_as_json(dict, filename):
    with open(filename + ".json", "w") as f:
        json.dump(dict, f, indent = 4)

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

    time_sta = time.perf_counter()

    import undetected_chromedriver.v2 as uc
    from pyvirtualdisplay import Display
    display = Display(visible=0, size=(800, 600))
    display.start()

    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    driver = uc.Chrome(use_subprocess=True)

    loded_end_id = get_loaded_end_id(dirname1)

    latest_id = get_latest_id(driver)
    print(f"loaded_last id : {loded_end_id}")
    print(f"latest id : {latest_id}")
    
    for id in range(max(loded_end_id, args.start), min(args.end, latest_id) + 1):
        print(f"loop id : {id}")
        tmp_url = f"{search_tmp_url}/{id}"
        driver.get(tmp_url)


        #画像保存
        img_src = get_imgsrc(driver)
        if img_src:
            download_img(img_src, f"{dirname}/{id:015}")

        #メタ情報保存
        od = OrderedDict()
        od["tags"]         = get_tag_all(driver) 
        od["informations"] = get_info(driver)
        if od:
            save_dict_as_json(od, f"{dirname1}/{id:015}")

    driver.quit()
    display.stop()

    time_end = time.perf_counter()

    print(time_end - time_sta)

