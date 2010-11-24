#encoding=utf-8
from config import Config
from testcase import TestCase
from logger import log
import os
import threading
import time
import sys

class Monitor:

  """
  初始化监控主程序，加载监控配置文件和设置工作环境。
  """
  def __init__(self,config=Config,**kwargs):
	self.config = config

	testdir = self.config.testdir
	# scan test file
	self.testcases = {} # 管理测试用例

	for testfile in self.get_test_files():
	  # 构造测试并添加，视情况看是否需要启用新定时器
	  xml = '' #TODO read xml from file
	  testcase = TestCase()
	  try:
		testcase.fromxml(xml)
		self.testcases[testcase.name] = testcase
	  except:
		log.error('invalid testcase definition in file : %s, will be discard.'%testfile)

	log.info('load test file done! there are %d valid testcases.'%len(self.testcases.keys()))

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

  def handle_result(self,result):
	log.debug('handling test result')

  def run(self):
	log.debug('about to run all test!')
	for name,testcase in self.testcases.items():
	  try:
		thread = threading.Thread(target=testcase,name=name,kwargs={'config':self.config,'callback':self.handle_result})
		thread.start()
	  except Exception,e:
		log.error('testcase %s start fail.'%name)
		excinfo = sys.exc_info()
		log.error(excinfo[0])
		log.error(excinfo[1])

	log.info( 'ok,it is your show time now,i gotta sleep')

	while threading.activeCount() > 1:
	  log.info( 'still %d people doing their job? just go on!'%threading.activeCount())
	  time.sleep(60)

	log.info('so,guys,have all your jobs don? now quit!')


if __name__ == '__main__':
  Monitor().run()
