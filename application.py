#encoding=utf-8
from config import Config
from testcase import TestCase
import os
import threading

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
		print 'invalid testcase definition in file : %s, will be discard.'%testfile

	print 'load test file done! there are %d valid testcases.'%len(self.testcases.keys())

  def get_test_files(self):
	testdir = self.config.testdir
	if not os.path.exists(testdir):
	  testdir = os.path.sep.join(__file__,testdir)
	  if not os.path.exists(testdir)
		raise Error,'testdir %s not found!'%self.config.testdir

	for file in os.listdir(testdir):
	  if file.endswith('test.xml'):
		yield os.path.sep.join(testdir,file)

  def handle_result(self,result):
	print 'handling test result'

  def run(self):
	for testcase in self.testcases:
	  try:
		thread = threading.Thread(target=testcase,name=testcase.name,kwargs={'config':self.config,'callback':self.handle_result})
		thread.start()
	  except:
		print 'testcase %s start fail.'%testcase.name


if __name__ == '__main__':
  Monitor().run()
