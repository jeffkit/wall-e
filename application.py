#encoding=utf-8
import urllib,urllib2
from monitor import Monitor

if __name__ == '__main__':
    # 演示结果处理器可以配置
    class Handler:
        pass
    rh = Handler()
    setattr(rh,'handle',lambda x:log.debug('handle result in your way!'))
    Monitor(result_handler=rh).run()

