#encoding=utf-8

"""
监控工作配置类，配置保存了监控程序运行时所需要的信息。
如，测试文件位置、调试模式等
"""
class MonitorConfig:

    def __init__(self,**kwargs):
        d = self.__dict__

        # set default config
        self.debug = 0

        self.testdir = 'testcases'

        self.http_timeout = 30

        self.master_check_time = 10 # 主线程检测是否还有工作进程的间隔时间，单位为秒

        for k,v in kwargs.items():
            if k[0] != '_': # 预防修改私有变量
                setattr(self,k,v)

    """
    设置属性时，在此可以做一些预处理
    """
    def __setattr__(self,name,value):
        d = self.__dict__

        d[name] = value

Config = MonitorConfig()
