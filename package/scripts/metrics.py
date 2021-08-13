# -*- coding: utf-8 -*-
import json, time, sys

params_data = sys.argv[1]
params_json = json.loads(params_data)

td_pid_file = params_json["tdengine"]["pid_file"]


# 检测进程并发送metrics数据
def check_and_send():
    # 当es进程不存在时，循环终止
    while check_process(td_pid_file):
        get_api_data()
        time.sleep(10)


if __name__ == "__main__":
    check_and_send()
