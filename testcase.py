#encoding=utf-8
from logger import log
import time
import os
from xml.dom import minidom
from utils import get_child_tags
from assertser import get_assertser
from sampler import get_sampler

test_components = {}

"""
测试结果
"""
class TestResult:
  def __init__(self):
	pass

class TestNode(object):

  def __init__(self,*args,**kwargs):
	self.parent = None # 父节点
	self.children = [] # 子节点
	self.context = {} # 该节点的上下文

	d = self.__dict__
	for k,v in kwargs.items():
	  d[k] = v

  def is_valid(self):
	return False

  def fromxml(self,xml):
	log.debug('setting attributes from xml')

	for k,v in xml.attributes.items():
	  self._append_attr(k,v)

	log.debug('parase child nodes')
	self.parse_child_tags(xml)

  def parse_child_tags(self,xml):

	for child_node in get_child_tags(xml):
	  if test_components.get(child_node.tagName,None):
		comp = test_components.get(child_node.tagName)()
		if getattr(comp,'fromxml',None):
		  comp.fromxml(child_node)
		  comp.parent = self
		  self.children.append(comp)
		elif getattr(self,'_parse_%s'%child_node.tagName,None):
		  # 如果是可解释的元素，则亲自解释,如attr
		  getattr(self,'_parse_%s'%child_node.tagName)(child_node)
		else:
		  # 没有实现fromxml方法
		  raise Exception,'function not implements:fromxml'
	  else:
		log.warn('unkown tag %s'%child_node.tagName)

  def _parse_attr(self,xml):
	log.debug('parse attribute')
	attrs = xml.attributes
	if attrs.has_key('name') and attrs.has_key('value'):
	  name = attrs['name']
	  value = attrs['value']
	  self.context[name] = value
	else:
	  log.warn('invalid attribute tag')

  def _parse_attribute(self,xml):
	self._parse_attr(xml)

  def _parse_parameter(self,xml):
	self._parse_attr(xml)


  def _append_attr(self,name,value):
	# 如果是一些已知的属性，可能需要做类型转换。未知的就是字符值。
	log.debug('setting attrbite %s=%s'%(name,value))
	d = self.__dict__
	if d.has_key(name):
	  log.debug('testcase attribute exists')
	  try:
		d[name] = type(d[name])(value)
	  except:
		pass
	else:
	  log.debug('testcase do not have a attribute %s'%name)
	  d[name] = value


"""
一个测试用例
"""
class TestCase(TestNode):

  def __init__(self,name=None,*args,**kwargs):
	# 设置默认参数
	self.name = name # 测试用例的名称
	self.loop = 1 # 反复执行测试次数，-1为无限循环
	self.frequency = 10 # 延迟60秒执行一次
	self.delay = 1 # 第一次执行的延迟时间

	self._test_count = 0

	# 每次测试需要使用的私有属性
	self._context = {} #测试上下文

	super(TestCase,self).__init__(*args,**kwargs)

  def is_valid(self):
	if self.children:
	  return True

  """
  每次测试前，需要做一些准备工作？
  """
  def setup(self):
	log.debug('in test steup')

  """
  每次测试完成后，清理现场
  """
  def teardown(self):
	log.debug('in test teardown')
	self._context.clear()

  """
  单次测试
  """
  def test(self):
	self.setup()

	log.debug('now testing')
	#TODO !important your test logic

	for child in self.children:
	  try:
		child()
	  except:
		# 此处要判断是否AssertionError，如果不是则是测试过程出错，而非断言错误
		pass

	self.teardown()

  """
  应用全局配置的原则是：
  对于某些配置属性，当测试用例没有显式配置时，使用全局配置
  """
  def apply_global_config(self,config):
	log.debug('applying global config')

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

	  log.debug('there are %d loop(s) left'%self.loop)

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
class Sample(TestNode):
  def __init__(self,type="HTTP",*args,**kwargs):
	self.type = type
	# TODO 新建的方式，也需要Mixin相应的采样器，考虑一下如何与parse_child_tags的结合起来

	super(Sample,self).__init__(*args,**kwargs)

  def parse_child_tags(self,xml):
	# 如果有相应的采样器，则把采样器的能力复制过来,这样，具体需要怎么解释就让采样器自己来搞定吧
	sampler_cls = get_sampler(self.type.lower())
	if sampler_cls:
	  self.__class__.__bases__ += (sampler_cls,)

	super(Sample,self).parse_child_tags(xml)

  """
  run the sampler
  """
  def __call__(self):
	pass



"""
一次断言
"""
class Assert(TestNode):
  def __init__(self,*args,**kwargs):

	super(Assert,self).__init__(*args,**kwargs)

  def fromxml(self,xml):
	pass

  """
  do assertion
  """
  def __call__(self):
	pass

test_components['test'] = TestCase
test_components['sample'] = Sample
test_components['assert'] = Assert

