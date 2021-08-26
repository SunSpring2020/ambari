# -*- coding: utf-8 -*-
from resource_management import *

config = Script.get_config()

# 获取tdengine-env.xml中的td_user用户变量
td_user = config['configurations']['tdengine-env']['td_user']

# 获取tdengine-env.xml中的td_group用户组变量
td_group = config['configurations']['tdengine-env']['td_group']

# 获取tdengine-env.xml的TDengine的安装文件夹
tdengine_dir = config['configurations']['tdengine-env']['tdengine_dir']

# 获取tdengine-env.xml的TDengine的配置文件路径
tdengine_config_dir = config['configurations']['tdengine-env']['tdengine_config_dir']
tdengine_config_file = format("{tdengine_config_dir}/taos.cfg")

# 获取tdengine-env.xml的TDengine数据文件夹
dataDir = config['configurations']['tdengine-env']['tdengine_data_dir']

# 获取tdengine-env.xml的TDengine日志文件夹
logDir = config['configurations']['tdengine-env']['tdengine_log_dir']

# 获取tdengine-env.xml的TDengine缓存文件文件夹
tempDir = config['configurations']['tdengine-env']['tdengine_temp_dir']

# 获取tdengine-env.xml的TDengine pid文件夹
tdengine_pid_dir = config['configurations']['tdengine-env']['tdengine_pid_dir']

# 获取tdengine-env.xml的TDengine pid文件
tdengine_pid_file = format("{tdengine_pid_dir}/tdengine.pid")

# 获取本机主机名称
fqdn = config['agentLevelParams']['hostname']

# RESTful连接器端口
httpPort = 6041

# 获取服务端口地址
serverPort = config['configurations']['tdengine-config']['serverPort']

# 可用于查询处理的总 CPU 核的比例
ratioOfQueryCores = config['configurations']['tdengine-config']['ratioOfQueryCores']

# 系统中mnode的数量
numOfMnodes = config['configurations']['tdengine-config']['numOfMnodes']

# 缓存块的大小
cache = config['configurations']['tdengine-config']['cache']

# 每个vnode节点的缓存块数量
blocks = config['configurations']['tdengine-config']['blocks']

# 每个 DB 文件的天数
days = config['configurations']['tdengine-config']['days']

# 数据文件保存时间
keep = config['configurations']['tdengine-config']['keep']

# 复制次数，仅适用于集群，针对mnode
replica = config['configurations']['tdengine-config']['replica']

# 获取ambari集群列表
hosts = config['clusterHostInfo']['all_hosts']

# 获取TDengine集群列表
tdHosts = config['clusterHostInfo']['tdengine_service_hosts']

# 获取首节点的FQDN
firstEp = tdHosts[0]

# metrics查询用户
ambari_metrics_user = "metrics_search"

# metrics查询用户密码
ambari_metrics_password = "metrics"

# metric服务地址
metrics_collector_host = default("/clusterHostInfo/metrics_collector_hosts", ['localhost'])[0]

# metric服务端口
metrics_collector_port = config['configurations']['ams-site']['timeline.metrics.service.webapp.address'].split(":")[1]

if config.get('repositoryFile'):
    baseUrl = config['repositoryFile']['repositories'][0]['baseUrl']
    tdengine_download = format("{baseUrl}/tdengine/TDengine-server-2.0.20.10-Linux-x64.tar.gz")
