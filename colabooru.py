import subprocess
import time
import shutil
import argparse
from google.colab import drive

#マウント
drive.mount("/content/drive")
save_dir = os.path.join("content", "drive", "MyDrive", "danbooru")

parser = argparse.ArgumentParser()
parser.add_argument("--workers", type=int, required=False, default=1)
parser.add_argument("--num", type=int, required=False, default=500)
args = parser.parse_args()

time_sta = time.perf_counter()
pro_sta = time.process_time()

try :
    cmd = f"python3 danbooru.py {save_dir} --num {args.num} --workers {args.workers}"
    subprocess.call(cmd.split())
except:
    print("途中終了")
finally:
    time_end = time.perf_counter()
    pro_end = time.process_time()

    total = time_end - time_sta
    pro_total = pro_end - pro_sta

    print(f"total = {total} , process_time = {pro_total}")
