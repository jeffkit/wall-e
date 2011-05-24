#encoding=utf-8
import urllib,urllib2
from monitor import Monitor
from resultHandler import xmlHandler
if __name__ == '__main__':
    rh = xmlHandler()
    Monitor(result_handler=rh).run()

