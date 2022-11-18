import subprocess
import time
import shutil
import argparse

time_sta = time.perf_counter()
pro_sta = time.process_time()


parser = argparse.ArgumentParser()
parser.add_argument("--workers", type=int, required=False, default=1)
parser.add_argument("--testdir", type=str, required=False, default="/mnt/okinawa/test_dir")
args = parser.parse_args()

try :
    cmd = f"python3 danbooru.py {args.testdir} --start 5000000 --end 5000500 --workers {args.workers}"
    subprocess.call(cmd.split())
except:
    print("途中終了")
finally:
    time_end = time.perf_counter()
    pro_end = time.process_time()

    total = time_end - time_sta
    pro_total = pro_end - pro_sta

    print(f"total = {total} , process_time = {pro_total}")

    shutil.rmtree(args.testdir)