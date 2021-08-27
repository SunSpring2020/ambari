# -*- coding: utf-8 -*-
import base64
import json, time, sys, logging, os, socket, requests

# 获取传入的参数
params_data = sys.argv[1]
params_json = json.loads(params_data)

# 从传入参数读取metrics_collector的ip
mc_ip = params_json['metrics_collector']['ip']
# 从传入参数读取metrics_collector的端口
mc_port = params_json['metrics_collector']['port']
# 拼接metrics_collector的请求地址
metrics_collector_api = "http://{0}:{1}/ws/v1/timeline/metrics".format(mc_ip, mc_port)
# 从传入参数读取td的pid文件
td_pid_file = params_json["tdengine"]["pid_file"]
# 从传入参数读取td的日志文件夹
td_log_dir = params_json["tdengine"]["log_dir"]
# 从传入参数读取专门用于metrics的查询用户
user = params_json["tdengine"]["user"]
# 从传入参数读取metrics查询用户的密码
password = params_json["tdengine"]["password"]
# 从传入参数获取本机的fqdn
fqdn = params_json["tdengine"]["fqdn"]
# 从传入参数获取TDengine的RESTful接口
httpPort = params_json["tdengine"]["httpPort"]
# 配置metrics的直至文件
metrics_log_file = "td_metrics.log"
metrics_log = os.path.join(td_log_dir, metrics_log_file)
# TDengine的RESTful接口的请求参数需要经过Base64编码
userToken = base64.b64encode("{0}:{1}".format(user, password))
# 拼接TDengine的RESTful请求路径
restful = "http://{0}:{1}/rest/sql".format(fqdn, httpPort)
# 拼接TDengine的RESTful请求头
header = {
    "Authorization": "Basic " + str(userToken)
}

if not os.path.exists(td_log_dir):
    os.makedirs(td_log_dir, 0644)

# 输出到console
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)  # 指定被处理的信息级别为最低级DEBUG，低于level级别的信息将被忽略
# 输出到文件
logging.basicConfig(level=logging.INFO,  # 控制台打印的日志级别
                    filename=metrics_log,
                    filemode='a',  ##文件模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                    # a是追加模式，默认如果不写的话，就是追加模式
                    format='%(asctime)s - %(filename)s [line:%(lineno)d] %(levelname)s: %(message)s',  # 日志格式
                    )
logger = logging.getLogger()
logger.addHandler(ch)


# 根据pid文件判断进程是否正常运行
def check_process(pid_file):
    # 判断pid文件是否存在
    if not pid_file or not os.path.isfile(pid_file):
        logger.error("Pid file {0} is empty or does not exist".format(str(pid_file)))
        return False

    # 获取pid文件中的pid进程号
    try:
        f = open(pid_file, 'r')
        pid = int(f.read())
    except:
        logging.error("Pid file {0} does not exist or does not contain a process id number".format(pid_file))
        return False
    finally:
        f.close()

    # 根据pid进程号判断对应进程是否存活
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        logging.error("Process with pid {0} is not running. Stale pid file at {1}".format(pid, pid_file))
        return False


#  获取TDengine的统计数据
def get_metrics_data():
    # 查询次数，列表
    req_select_sql = "select sum(req_select) from log.dn where ts >= now-10m and ts < now interval(1m)"
    # 写入次数，列表
    req_insert_sql = "select sum(req_insert) from log.dn where ts >= now-10m and ts < now interval(1m)"
    # taosd服务内存，数字
    taosd_memory_sql = "select max(mem_taosd) from log.dn where ts >= now -10m and ts < now"
    # 系统内存，数字
    system_memory_sql = "select max(mem_system) from log.dn where ts >= now -10m and ts < now"
    # 系统CPU，列表
    cpu_system_sql = "select avg(cpu_system) from log.dn where ts >= now-10m and ts < now  interval(1s)"
    # taosd占用CPU，列表
    cpu_taosd_sql = "select avg(cpu_taosd) from log.dn where ts >= now-10m and ts < now  interval(1s)"
    # 硬盘使用，列表
    disk_used_sql = "select avg(disk_used) disk_used from log.dn where ts >= now-10m and ts < now interval(1s)"
    try:
        # 查询次数，列表
        # response_req_select = json.loads(requests.post(restful, data=req_select_sql, headers=header).content)
        # 写入次数，列表
        # response_req_insert = json.loads(requests.post(restful, data=req_insert_sql, headers=header).content)
        # taosd服务内存，数字
        response_taosd_memory = json.loads(requests.post(restful, data=taosd_memory_sql, headers=header).content)
        taosd_memory = response_taosd_memory['data'][0][0]
        send_metric_to_collector("taosd.memory", taosd_memory)
        # 系统内存，数字
        response_system_memory = json.loads(requests.post(restful, data=system_memory_sql, headers=header).content)
        system_memory = response_system_memory['data'][0][0]
        send_metric_to_collector("system.memory", system_memory)
        # 系统CPU，列表
        # response_cpu_system = json.loads(requests.post(restful, data=cpu_system_sql, headers=header).content)
        # taosd占用CPU，列表
        # response_cpu_taosd = json.loads(requests.post(restful, data=cpu_taosd_sql, headers=header).content)
        # 硬盘使用，列表
        # response_disk_used = json.loads(requests.post(restful, data=disk_used_sql, headers=header).content)
    except Exception as e:
        logging.error(e)


# 发送指标数据到metrics collector
def send_metric_to_collector(metric_name, metric_data):
    appid = "tdengine"
    millon_time = int(time.time() * 1000)
    hostname = socket.gethostname()
    header = {
        "Content-Type": "application/json"
    }
    metrics_json = {
        "metrics": [
            {
                "metricname": metric_name,
                "appid": appid,
                "hostname": hostname,
                "timestamp": millon_time,
                "starttime": millon_time,
                "metrics": {
                    millon_time: metric_data
                }
            }
        ]
    }
    logging.info("[{0}] send metrics to collector data: {1}".format(metric_name, metrics_json))
    try:
        resp = requests.post(metrics_collector_api, json=metrics_json, headers=header)
        logging.info("send metrics result: {0}".format(resp.content))
    except Exception as e:
        logging.error("send metrics failure: {0}".format(e))
        pass


# 检测进程并发送metrics数据
def check_and_send():
    # 当tdengine进程不存在时，循环终止
    while check_process(td_pid_file):
        try:
            get_metrics_data()
        except Exception:
            pass
        time.sleep(10)


if __name__ == "__main__":
    check_and_send()
