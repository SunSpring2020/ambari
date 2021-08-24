# -*- coding: utf-8 -*-
import json, os

from resource_management import *


class Master(Script):

    def install(self, env):
        import params
        env.set_params(params)

        Logger.info("安装开始")

        # 配置以及安装前的必要检查
        # 1、判断Tdengine的安装数量是否为奇数个
        if len(params.tdHosts) % 2 == 0:
            raise Exception("Tdengine的集群数量不能是偶数个")
        # 2、判断配置中的firstEq是否在Tdengine的安装列表中
        boo = 0
        firstEqTmp = params.firstEp.encode('utf8').strip()
        for x in params.tdHosts:
            temp = str(x)
            if (temp == firstEqTmp) | (temp is firstEqTmp):
                boo = 1

        if boo == 0:
            raise Exception("firstEq不在Tdengine安装集群")

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

        try:
            Execute('systemctl start taosd')
        except:
            Execute("service taosd start")

        fqdn = params.fqdn.encode('utf8').strip()

        if (firstEqTmp == fqdn) | (firstEqTmp is fqdn):
            for x in params.tdHosts:
                temp = str(x).encode('utf8').strip()
                if (firstEqTmp != temp) & (firstEqTmp is not temp):
                    Execute("taos -s \"create dnode \"" + temp + "\"\"")

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

        Logger.info("配置结束")

    def start(self, env):
        import params
        env.set_params(params)

        Logger.info("启动开始")

        # 启动前的配置
        self.configure(env)

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
                "port": params.serverPort,
                "pid_file": params.tdengine_pid_file,
                "log_dir": params.logDir
            },
            "metrics_collector": {
                "ip": "ambari01",
                "port": "123"
            }
        }

        current_dir = os.path.dirname(os.path.abspath(__file__))

        cmd = "nohup /usr/bin/python -u {0}/metrics.py '{1}' > /dev/null 2>&1 &".format(current_dir,
                                                                                        json.dumps(params_data))

        Execute(cmd)

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
