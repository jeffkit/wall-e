#encoding=utf-8
import time

"""
一个测试用例
"""
class TestCase:

  def __init__(self,name=None,*args,**kwargs):
	# 设置默认参数
	self.name = name # 测试用例的名称
	self.loop = 1 # 反复执行测试次数，-1为无限循环
	self.frequency = 60 # 延迟60秒执行一次
	self.delay = 10 # 第一次执行的延迟时间

	self._test_count = 0

  def fromxml(self,xml):
	print 'in fromxml'

  """
  每次测试前，需要做一些准备工作？
  """
  def setup(self):
	print 'in test steup'

  """
  每次测试完成后，清理现场
  """
  def teardown(self):
	print 'in test teardown'

  def test(self):
	self.setup()

	print 'now testing'
	#  your test logic

	self.teardown()

  """
  应用全局配置的原则是：
  对于某些配置属性，当测试用例没有显式配置时，使用全局配置
  """
  def apply_global_config(config):
	pass

  """
  测试进程会调用此方法
  主要工作是：
  在循环次数还没达到的时候，每隔一段时间执行一次测试
  """
  def __call__(self,config=None,callback=None):

	if config:
	  self.apply_global_config(config)

	time.sleep(self.delay)
	while self.loop == -1 or self.loop > 0:
	  result = self.test()
	  if callback:
		callback(result)

	  self._test_count += 1
	  if self.loop > 0:
		self.loop -= 1

	  time.sleep(self.frequency)

"""
一次远程采样
"""
class Sample:
  def __init__(self,*args,**kwargs):
	pass

  def fromxml(self,xml):
	pass


"""
一次断言
"""
class Assert:
  def __init__(self,*args,**kwargs):
	pass

  def fromxml(self,xml):
	pass
