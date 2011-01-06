#encoding=utf-8
from config import Config
from testcase import TestCase
from logger import log,log_exce
from utils import get_child_tags
import os
import threading
import time
import sys
import urllib,urllib2
from xml.dom import minidom

class Monitor:

    """
    初始化监控主程序，加载监控配置文件和设置工作环境。
    """
    def __init__(self,config=Config,result_handler=None,**kwargs):
        self.config = config
        if result_handler and getattr(result_handler,'handle',None):
            self.result_handler = result_handler

        testdir = self.config.testdir
        # scan test file
        self.testcases = {} # 管理测试用例

        for testfile in self.get_test_files():
        # 构造测试并添加，视情况看是否需要启用新定时器
            testcase = TestCase()
            try:
                xml = self.parsexml(testfile)
                testcase.fromxml(xml)
                if testcase.is_valid():
                    self.testcases[testcase.name] = testcase
                else:
                    raise Exception,'no testcase found of empty testcase'
            except:
                log_exce('invalid testcase definition in file : %s, will be discard.'%testfile)

        log.info('load test file done! there are %d valided testcases.'%len(self.testcases.keys()))

    def get_test_files(self):
        testdir = self.config.testdir
        if not os.path.exists(testdir):
            testdir = os.path.sep.join((__file__,testdir))
            if not os.path.exists(testdir):
                msg = 'testdir %s not found!'%self.config.testdir
                log.error(msg)
                raise Exception,msg

        for file in os.listdir(testdir):
            if file.endswith('test.xml'):
                yield os.path.sep.join((testdir,file))

    """
    从XML生成TestCase的内容，xml参数可能是文本，也可能是一个文件
    """
    def parsexml(self,xml):
        log.debug('in parsexml')
        # 如果传进来的是文件，则直接读取内容
        # 如果是字符串，则先尝试解释，如果不是xml则再尝试作为文件路径，再不行，则抛异常了。
        xml_content = ''
        if type(xml) == file:
            xml_content = xml.read()
            xml.close()
        elif type(xml) == str or type(xml) == unicode:
            log.debug('try to load file')
            if os.path.exists(xml):
                xml_file = open(xml,'r')
                xml_content = xml_file.read()
                xml_file.close()
            else:
                xml_content = xml
        else:
            log.error('could not init testcase from xml')
            raise TypeError,'fromxml need a file instance or a string instance for argument'

        log.debug('starting parse xml')
        log.debug('xml content: %s'%xml_content)
        doc = minidom.parseString(xml_content)

        ret = get_child_tags(doc,'test')
        log.debug('child tag len : %d'%len(ret))

        if ret:
            test_node = ret[0]
            return test_node
        else:
            log.warn('no test node in the xml!')

    def handle_result(self,result):
        log.debug('handling test result')
        if getattr(self,'result_handler',None):
            log.debug('delegate result to somebody')
            try:
                self.result_handler.handle(result)
            except:
                log.debug('fail to handle result by a custom handler,we will handle the result in default way.')
                self.result2xml(result)
        else:
            log.debug('handle result in the default way,save as xml file')
            self.result2xml(result)

    def result2xml(self,result):
        log.debug('save test result to xml')

    def run(self):
        log.debug('about to run all test!')
        for name,testcase in self.testcases.items():
            try:
                thread = threading.Thread(target=testcase,name=name,kwargs={'config':self.config,'callback':self.handle_result})
                thread.start()
            except Exception,e:
                log_exce('testcase %s start fail.'%name)

        log.info( 'ok,it is your show time now,i gotta sleep')

        while threading.activeCount() > 1:
            log.info( 'still %d people doing their job? just go on!'%threading.activeCount())
            time.sleep(self.config.master_check_time)

        log.info('so,guys,have all your jobs don? now quit!')

