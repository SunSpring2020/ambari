# -*- coding: utf-8 -*-
import json, os
import time

from resource_management import *


class Master(Script):

    def install(self, env):
        import params
        env.set_params(params)

        Logger.info("安装开始")

        # 配置以及安装前的必要检查:判断Tdengine的安装数量是否为奇数个
        if len(params.tdHosts) % 2 == 0:
            raise Exception("Tdengine的集群数量不能是偶数个")

        # 删除旧程序
        Execute("rmtaos", ignore_failures=True)

        # 删除旧的配置文件
        Execute(format("rm -rf {tdengine_config_file}"))

        # 删除旧的数据文件
        Execute(format("rm -rf {dataDir}"))

        # 删除旧的日志文件
        Execute(format("rm -rf {logDir}"))

        # 删除可能残留的缓存目录
        Execute(format("rm -rf {tempDir}"))

        # 删除可能残留的安装文件目录
        Execute("rm -rf /opt/tdengine")

        # 获取安装包文件
        Execute(format('wget {tdengine_download} -O tdengine.tar.gz'))

        # 创建安装文件目录
        Execute('mkdir -p /opt/tdengine')

        # 创建缓存目录
        Execute(format("mkdir -p {tempDir}"))

        # 安装包文件解压并复制到安装文件目录
        Execute(format('tar -zxvf tdengine.tar.gz -C /opt/tdengine'))

        # 删除安装包文件
        Execute("rm -rf tdengine.tar.gz")

        # 修改安装目录
        tdengine_dir_tmp = params.tdengine_dir.replace("/", "\/")
        Execute(format("sed -i 's/\/usr\/local\/taos/{tdengine_dir_tmp}/g' /opt/tdengine/install.sh"))

        # 修改配置文件目录
        tdengine_config_dir_tmp = params.tdengine_config_dir.replace("/", "\/")
        Execute(format("sed -i 's/\/etc\/taos/{tdengine_config_dir_tmp}/g' /opt/tdengine/install.sh"))

        # 必须先打开该文件夹，否则执行install.sh会报：File taos.tar.gz does not exist
        Execute("cd /opt/tdengine && ./install.sh -e no")

        # 删除安装文件目录
        Execute("rm -rf /opt/tdengine")

        # 执行集群搭建配置
        configurations = params.config['configurations']['tdengine-config']
        File(format("{tdengine_config_file}"),
             content=Template("taos.cfg.j2", configurations=configurations))

        # 启动集群，进行集群搭建
        try:
            Execute('systemctl start taosd')
        except:
            Execute("service taosd start")

        fqdn = params.fqdn.encode('utf8').strip()

        firstEqTmp = params.firstEp.encode('utf8').strip()

        # 集群搭建
        if (firstEqTmp == fqdn) | (firstEqTmp is fqdn):
            # 将非firstEq的节点加入到集群
            for x in params.tdHosts:
                temp = str(x).encode('utf8').strip()
                if (firstEqTmp != temp) & (firstEqTmp is not temp):
                    Execute("taos -s \"create dnode \"" + temp + "\"\"")
            # 创建metrics查询用户
            Execute(format("taos -s \"CREATE USER {ambari_metrics_user} PASS \'{ambari_metrics_password}\'\""))
            # 给metrics查询用户赋权，只给予读权限
            Execute(format("taos -s \"ALTER USER {ambari_metrics_user} PRIVILEGE read\""))

        # 下载安装python requests模块需要的安装包（已在本地源内部配置）
        Execute(format("wget {baseUrl}/python/setuptools-44.1.1.zip"))
        Execute(format("wget {baseUrl}/python/certifi-2021.5.30.tar.gz"))
        Execute(format("wget {baseUrl}/python/chardet-4.0.0.tar.gz"))
        Execute(format("wget {baseUrl}/python/idna-2.10.tar.gz"))
        Execute(format("wget {baseUrl}/python/urllib3-1.26.6.tar.gz"))
        Execute(format("wget {baseUrl}/python/requests-2.26.0.tar.gz"))
        # 解压安装包
        Execute("unzip -o -q setuptools-44.1.1.zip")
        Execute("tar -zxvf certifi-2021.5.30.tar.gz")
        Execute("tar -zxvf chardet-4.0.0.tar.gz")
        Execute("tar -zxvf idna-2.10.tar.gz")
        Execute("tar -zxvf urllib3-1.26.6.tar.gz")
        Execute("tar -zxvf requests-2.26.0.tar.gz")
        # 删除安装包
        Execute("rm -rf setuptools-44.1.1.zip")
        Execute("rm -rf certifi-2021.5.30.tar.gz")
        Execute("rm -rf chardet-4.0.0.tar.gz")
        Execute("rm -rf idna-2.10.tar.gz")
        Execute("rm -rf urllib3-1.26.6.tar.gz")
        Execute("rm -rf requests-2.26.0.tar.gz")
        # requests安装
        Execute("cd setuptools-44.1.1 && python setup.py install")
        Execute("cd certifi-2021.5.30 && python setup.py install")
        Execute("cd chardet-4.0.0 && python setup.py install")
        Execute("cd idna-2.10 && python setup.py install")
        Execute("cd urllib3-1.26.6 && python setup.py install")
        Execute("cd requests-2.26.0 && python setup.py install")
        # 删除安装文件夹
        Execute("rm -rf setuptools-44.1.1")
        Execute("rm -rf certifi-2021.5.30")
        Execute("rm -rf chardet-4.0.0")
        Execute("rm -rf idna-2.10")
        Execute("rm -rf urllib3-1.26.6")
        Execute("rm -rf requests-2.26.0")

        Logger.info("安装完成!")

    def configure(self, env):
        import params
        env.set_params(params)

        Logger.info("配置开始")

        Directory([params.tdengine_pid_dir],
                  mode=0755,
                  cd_access='a',
                  owner=params.td_user,
                  group=params.td_group,
                  create_parents=True)

        configurations = params.config['configurations']['tdengine-config']
        File(format("{tdengine_config_file}"),
             content=Template("taos.cfg.j2", configurations=configurations))

        # 修改各个文件夹的权限
        Execute(
            format("chown -R {td_user}:{td_group} {tdengine_dir} {tdengine_config_dir} {dataDir} {logDir} {tempDir}"))

        Logger.info("配置结束")

    def start(self, env):
        import params
        env.set_params(params)

        Logger.info("启动开始")

        # 启动前的配置
        self.configure(env)

        time.sleep(10)

        # taosd服务启动
        try:
            Execute('systemctl start taosd')
        except:
            Execute("service taosd stop")

        # 获取taosd服务的pid并写入文件
        cmd = "ps -ef | grep /usr/bin/taosd | grep -v grep | awk '{print $2}' > " + params.tdengine_pid_file
        Execute(cmd)

        # 构建参数，执行metrics循环发送数据
        params_data = {
            "tdengine": {
                "pid_file": params.tdengine_pid_file,
                "log_dir": params.logDir,
                "user": params.ambari_metrics_user,
                "password": params.ambari_metrics_password,
                "fqdn": params.fqdn,
                "httpPort": params.httpPort
            },
            "metrics_collector": {
                "ip": params.metrics_collector_host,
                "port": params.metrics_collector_port
            }
        }

        current_dir = os.path.dirname(os.path.abspath(__file__))

        Execute("nohup /usr/bin/python -u {0}/metrics.py '{1}' > /dev/null 2>&1 &".format(current_dir,
                                                                                          json.dumps(params_data)))

        Logger.info("启动结束")

    def stop(self, env):
        import params
        env.set_params(params)

        Logger.info("停止开始")

        # taosd服务停止
        try:
            Execute('systemctl stop taosd')
        except:
            Execute("service taosd stop")

        # taosd的pid文件夹删除
        Directory([params.tdengine_pid_dir], action="delete")

        Logger.info("停止结束")

    def status(self, env):
        import status_params
        env.set_params(status_params)

        check_process_status(status_params.tdengine_pid_file)

    def restart(self, env):
        Logger.info("重启开始")

        self.stop(env)
        self.start(env)

        Logger.info("重启结束")


if __name__ == "__main__":
    Master().execute()
