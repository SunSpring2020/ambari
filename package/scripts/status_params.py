# -*- coding: utf-8 -*-
from resource_management import *

config = Script.get_config()

# 获取tdengine-env.xml的tdengine_pid_dir es pid文件夹
tdengine_pid_dir = config['configurations']['tdengine-env']['tdengine_pid_dir']

tdengine_pid_file = format("{tdengine_pid_dir}/tdengine.pid")
