#encoding=utf-8
from logger import log,log_exce
import time
import os
import sys
from xml.dom import minidom
from utils import get_child_tags
from asserter import get_asserter,TestAssertionError
from sampler import get_sampler
from datetime import datetime
from resultformat import MutiFormat
#from warning import warn2email
#from warning import warn2db
register_node = {}

def register(name,node_cls):
    if TestNode not in node_cls.__bases__:
        raise Exception,'node_cls must be a TestNode subclass'
    register_node[name] = node_cls

def unregister(name):
    del register_node[name]

def get_registed_node(name):
    return register_node.get(name,None)

#判断是否详细记录结果
def islog(obj,arg=None):
    if getattr(obj,'log',None):
        log = getattr(obj,'log',None)
        if log.upper() in ['y','YES','TRUE','T']:
	        return True
        elif log.upper() in ['N','NO','FALSE','F']:
            return False
    elif arg is not None: 
        return arg
    else:
        return False

'''
class TestAssertionError(Exception):
    pass
'''

def wrap(value):
    class Wrapper(value.__class__):
        def __init__(self,v,*arg,**kwargs):
            self._data = [v]
            super(Wrapper,self).__init__(*arg,**kwargs)
            if getattr(v,'__dict__',None):
                self.__dict__.update(v.__dict__)
        def __iter__(self):
            return self._data.__iter__()
        def next(self):
            return obj._data.next()
    return Wrapper(value)

"""
测试结果
"""
class TestResult(MutiFormat):
    def __init__(self,type='test'):
        self.type = type
        self.status = 'SUCCESS' # or FAIL,ERROR
        self.sections = [] #测试的每一步详情,每个元素都是TestResult
    '''
    def toxml(self):
        # 输出XML格式的结果
        pass
    '''

class TestNode(object):

    def __init__(self,name=None,parent=None,*args,**kwargs):
        self._name = name
        self._parent = parent # 父节点
        self._children = [] # 子节点
        self._child_tags = set([])
        self._context = {} # 该节点的上下文

        self.__dict__.update(kwargs)

    def __str__(self):
        return '%s -- a %s instance'%(self._name,self.__class__.__name__)

    def __getattr__(self,name):
        #log.debug('####### WOO, why you are here? in __getattr__ ###### %s'%name)
        d = self.__dict__
        if name.endswith("_as_list") and d.has_key(name[0:name.index("_as_list")]):
            target = d[name[0:name.index('_as_list')]]
            if type(target) in (list,tuple):
                return target
            else:
                return (target,)

        try:
            return d[name]
        except KeyError:
            raise AttributeError(name)


    def fromxml(self,xml):
        log.debug('=================== starting parse xml, tag:%s ================'%self._name)

        if not self._name:
            self._name = xml.tagName

        for k,v in xml.attributes.items():
            print '--------------------[xml]-------------'
            print k,' ',v
            print '--------------------[xml]-------------'
            self._append_attr(k,v)
        log.debug('parase child nodes')
        self.parse_child_tags(xml)

        if not self._children:
            # if there are not child tags,try to get text
            self.parse_child_text(xml)

        if self._parent:
            self._parent._add_or_append_attr(self._name,self)

        log.debug('================== finish xml parse, tag:%s ==================='%self._name)

    def parse_child_text(self,xml):
        """
        >>> cdata = '''<data type="json">
        ... <![CDATA[ {"name":"jeff","password":"password"}]]>
        ... </data>
        ... '''
        >>> cdoc = minidom.parseString(cdata)
        >>> node = TestNode()
        >>> node.parse_child_text(cdoc.firstChild)
        >>> node._text
        u'{"name":"jeff","password":"password"}'
        >>> tdata = '<data type="text">hello world</data>'
        >>> tdoc = minidom.parseString(tdata)
        >>> node = TestNode()
        >>> node.parse_child_text(tdoc.firstChild)
        >>> node._text
        u'hello world'
        """
        # 如果有CDATA则只读CDATA，否则读所有TEXT结点
        log.debug('parse child text now')
        for child_node in xml.childNodes:
            if child_node.nodeType == xml.CDATA_SECTION_NODE:
                self._text = child_node._get_data().strip()
        if not getattr(self,'_text',None):
            log.debug('no CDATA found,try Text tag')
            for child_node in xml.childNodes:
                if child_node.nodeType == xml.TEXT_NODE:
                    self._text = child_node.wholeText.strip()
                    log.debug('my _text is :%s'%self._text)
                    return
                else:
                    log.debug('not text found too')

    def parse_child_tags(self,xml):
        """
        """
        for child_node in get_child_tags(xml):

            # 1.把未定义的标签转换成TestNode，当作当前结点的属性
            if get_registed_node(child_node.tagName):
                comp = get_registed_node(child_node.tagName)(name=child_node.tagName,parent=self)
            else:
                comp = TestNode(name=child_node.tagName,parent=self)

            # 这里可以把不需特别处理的Tag处理成当前节点的属性
            comp.fromxml(child_node)
            self._children.append(comp) # 所有Child放在一个List
            self._child_tags.add(child_node.tagName)
            #self._add_or_append_attr(child_node.tagName,comp) # 标签名相同的Child放在一个List

            # 2.看是否有相应的_parse方法提供，有则调用,作特别处理
            if getattr(self,'_parse_%s'%child_node.tagName,None):
                # 如果是可解释的元素，则亲自解释,如attr
                getattr(self,'_parse_%s'%child_node.tagName)(child_node)


    def _add_or_append_attr(self,name,value):
        """
        增加或追加属性
        """
        log.debug('add or append %s'%name)
        obj = getattr(self,name,None)
        if obj:
            if type(obj) in (list,tuple):
                obj += (value,)
            else:
                obj = (obj._data[0],value)
        else:
            obj = wrap(value)
        setattr(self,name,obj)

    def _parse_attr(self,xml):
        log.debug('parse attribute')
        attrs = xml.attributes
        if attrs.has_key('name') and attrs.has_key('value'):
            name = attrs['name']
            value = attrs['value']
            parent._context[name] = value
        else:
            log.warn('invalid attribute tag')

    def _parse_attribute(self,xml):
        self._parse_attr(xml)

    def _parse_parameter(self,xml,parent=None):
        self._parse_attr(xml)


    def _append_attr(self,name,value):
        # 如果是一些已知的属性，可能需要做类型转换。未知的就是字符值。
        log.debug('setting attrbite %s=%s'%(name,value))
        d = self.__dict__
        if d.has_key(name) and d[name] is not None:
            log.debug('testcase attribute exists')
            try:
                d[name] = type(d[name])(value)
            except:
                pass
        else:
            log.debug('testcase do not have a attribute %s or the attribute is None'%name)
            d[name] = value

"""
一个测试用例
"""
class TestCase(TestNode):

    def __init__(self,testname=None,*args,**kwargs):
        # 设置默认参数
        self.name = testname # 测试用例的名称
        self.loop = 1 # 反复执行测试次数，-1为无限循环
        self.frequency = 10 # 延迟60秒执行一次
        self.delay = 1 # 第一次执行的延迟时间
        self.cookies_enable = True
        self.timeout = 30

        self._test_count = 0

        super(TestCase,self).__init__(name='test',*args,**kwargs)


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

    def is_valid(self):
        return True

    """
    单次测试
    """
    def test(self):
        self.setup()

        log.debug('now testing')

        result = TestResult()
        result.testcase = self
        result.start_time = datetime.now()
        result.log = islog(self)
        log.debug('there are %s children in this testcase'%len(self._children))
        for child in self._children:
            log.debug('calling child %s'%child._name)
            try:
                rs = child()
                self.setResult(child,result,rs)
                if rs.status in ['ERROR','FAIL']:
                    print '=============error======'
                    # 测试组件自检出错
                    result.status = rs.status
                    #result.exc_info = rs.exc_info
                    log.debug('Test Error')
                    break
            except:
                # 而非断言错误,测试组件没能自检出来
                import sys
                result.status = 'ERROR'
                result.exc_info = sys.exc_info()
                log.debug('Test Error')
                log_exce()
                break
        result.end_time = datetime.now()
        self.teardown()
        #result.nodename = self.name
        #result.testcase = self
        return result

    #设置callback中的result
    def setResult(self,child,result,rs):
        if child._name in [u'sample','sample']:
            rs.nodetype = 'sample'
            rs._sample = child
            rs.log = islog(child,result.log)
       
        else:
            rs.nodetype = 'assert'
            rs._assert = child
          
	    result.sections.append(rs)

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
            '''
            if result.status in ['FAIL','ERROR']:
                #warn2email.warning(result)
                warn2db.warning(result)
            '''
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
    def __init__(self,type=None,*args,**kwargs):
        self.type = type
        if self.type:
            self.apply_sampler()
        super(Sample,self).__init__(*args,**kwargs)
        self.timeout = 30
        

    def apply_sampler(self):
        # 如果有相应的采样器，则把采样器的能力复制过来,这样，具体需要怎么解释就让采样器自己来搞定吧
        sampler_cls = get_sampler(self.type.lower())
        if sampler_cls and sampler_cls not in self.__class__.__bases__: 
	        sampler = type(str(self.type.upper())+'Sampler',(Sample,),{})
	        self.__class__ = sampler
	        self.__class__.__bases__ += (sampler_cls,)

    def parse_child_tags(self,xml):
        self.apply_sampler()

        super(Sample,self).parse_child_tags(xml)

    def _parse_data(self,xml):
        """
        >>> sample = Sample()
        >>> xml = '''<data type="xml"><item name="name" value="jeff"/><item name="password">password</item><item>hello</item><item>world</item></data>'''
        >>> doc = minidom.parseString(xml)
        >>> data = TestNode('data',sample)
        >>> data.fromxml(doc.firstChild)
        >>> sample._parse_data(doc.firstChild)
        >>> sample.data.kwargs == {u'name':u'jeff',u'password':u'password'}
        True
        >>> sample.data.args == [u'hello',u'world']
        True
        """
        self.data.args = []
        self.data.kwargs = {}

        data_type = getattr(self.data,'type','xml')
        if data_type == 'xml' and getattr(self.data,'item',None):
            for item in self.data.item:
                value = getattr(item,'value',None) or item._text
                if getattr(item,'name',None):
                    self.data.kwargs[item.name] = value
                else:
                    self.data.args += (value,)

        elif data_type == 'json':
            import simplejson as json
            #import json
            rs = json.loads(data._text)
            if type(rs) == dict:
                self.data.kwargs.update(rs)
            elif type(rs) in (list,tuple):
                self.data.args = rs
            else:
                pass


    """
    run the sampler
    """
    def __call__(self):
        return self.sample()

"""
一次断言
"""
class Assert(TestNode):

    """
    do assertion
    """

    def __call__(self):
        # 检测assert的类型，调用不同的assertser的方法就可以。
        log.debug('asserting ...')
        result = TestResult(self._name)
        try:
            assertser = get_asserter(self.type)
            self.getData()
            args = [item._text for item in self.item]
            
            assertser(*args)
        except AssertionError:
            result.status = 'FAIL'
            #result.exc_info = sys.exc_info()
            #result.exc_info[1].message = 'the len of the assert\'s item !=2'
        except TestAssertionError:
            # get AssertionError,说明测试失败,只能让asserter 抛出
            result.status = 'FAIL'     
        except KeyError:
            result.status = 'FAIL'
            result.exc_info = sys.exc_info()
            result.exc_info[1].message = 'not exists key \''+result.exc_info[1].message+'\' in this assert\'s item'
        except AttributeError:
            result.status = 'FAIL'
            result.exc_info = sys.exc_info()
            result.exc_info[1].message = 'not exists Attribute \''+result.exc_info[1].message+'\' in this assert'
        return result

    #对上面进行改进，对soap也适用
    def getData(self): 
        if len(self.item) != 2: return
        for item in self.item:
            if '${' and '}' in item._text :
                text = self.search(item._text[2:-1])
                item._text = text
                print 'text: ',item._text
        #print 'item: ',self.item
        '''
                text = item._text[2:-1]
                if self._context.has_key(text):
                    text = self._context[text]
                elif self._parent._context.has_key(text):
                    text = self._parent._context[text]
                    print 'text: ',text
                    print 'context: ',self._parent._context
                else: #处理soap断言
                    text = self.search(text)
                if text.__class__ is not unicode:
                    text = unicode(str(text),'utf-8')
                item._text = text
        '''


    def search(self,string):
        args = string.split('.')
        print 'args: ',args
        value = None
        print 'context: ',self._parent._context
        for item in args:
            if value:
                value = value[item]
            else:
            
                if self._context.has_key(item):
                    value = self._context[item]
                elif self._parent._context.has_key(item):
                    value = self._parent._context[item]
            print 'value: ',value
        return str(value)
    '''
        from SOAPpy import Types
        arg = string.split('.')
        for l in range(len(arg)):
            if '[' and ']' in arg[l-1]:
                index = arg[l-1][arg[l-1].index('[')+1:arg[l-1].index(']')]
                arg[l-1] = arg[l-1][:arg[l-1].index('[')]
                arg.insert(1,int(index))
            else:continue
        obj = None
        print 'arg: ',arg
        for i in range(len(arg)):
            if i == 0:
                if self._context.has_key(arg[i]):
                    obj = self._context[arg[i]]
                elif self._parent._context.has_key(arg[i]):
                    obj = self._parent._context[arg[i]]
            else:
                if type(obj) in [list,tuple] and type(arg[i]) in [int, long]:
                    obj = obj[arg[i]]
                elif obj.__class__ is Types.structType:
                    obj = obj.__dict__[arg[i]] 
        return obj
    '''
	
# 注册配置结点类
register('sample',Sample)
register('assert',Assert)

if __name__ == '__main__':
    import doctest
    log.debug('hello')
    doctest.testmod(verbose=True)


