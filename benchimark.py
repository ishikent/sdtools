import subprocess
import time
import shutil

time_sta = time.perf_counter()
pro_sta = time.process_time()

test_dir = "test_dir"

cmd = f"python3 danbooru.py {test_dir} --start 5000000 --end 5000500"
subprocess.call(cmd.split())

time_end = time.perf_counter()
pro_end = time.process_time()

total = time_end - time_sta
pro_total = pro_end - pro_sta

print(f"total = {total} , process_time = {pro_total}")

shutil.rmtree(test_dir)