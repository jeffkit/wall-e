#encoding=utf-8
import urllib
import urllib2
import socket
import os
import re
from SOAPpy import WSDL
from logger import log,log_exce
from datetime import datetime
from SOAPpy import Types

sampler_map = {}
 
def register(name,sampler):
    sampler_map[name] = sampler

def unregister(name):
    del sampler_map[name]

def get_sampler(name):
    return sampler_map[name]

def verify_ip(ip):
    el = r'(([0-9]|[0-1][0-9]{1,2}|2[0-4][0-9]|25[0-5])[.]){3}([0-9]|[0-1][0-9]{1,2}|2[0-4][0-9]|25[0-5])'
    r = re.search(el,ip)
    return r.group(0)

#定义参数异常类
class argsException(Exception):pass

#简单的类型校验
def convert(v=None,t=None):
    return v
    '''
    if v is None:return None
    elif t.lower()=='string':return str(v)
    elif t.lower() =='int':return int(v)
    elif t.lower() =='float':return float(v)
    elif t.lower()=='bool':
        if v.lower() in ['t','true','y','yes']:
            return True
        else:return False
    else:return str(v)
    '''
 
#定义继承BodyType的类型
class argObj(Types.bodyType):pass

# ============ Sampler定义，这些类均不应直接实例化，是被Mixin到Sample类里面使用的 ============

class HTTPSampler(object):

    # 在此判断所需要的信息是否完整
    def is_valid(self):
        return True

    # 采样的逻辑
    def sample(self):
        """
        HTTP 采样的逻辑
        >>> from testcase import Sample,TestCase,TestNode
        >>> test = TestCase()
        >>> sample = Sample(parent=test,type='http',url='http://www.botwave.com',method='GET')
        >>> headers = TestNode(name='headers',parent=sample)
        >>> item = TestNode(name='item',parent=headers)
        >>> item.name = 'User-Agent'
        >>> item.value = 'User-Agent: Mozilla/5.0 (Linux; X11)'
        >>> headers._add_or_append_attr('item',item)
        >>> sample.headers = headers
        >>> data = TestNode(name='data',parent=sample)
        >>> data.kwargs = {'name':'jeff','password':'hello'}
        >>> #sample.data = data
        >>> sample.url
        'http://www.botwave.com'
        >>> sample()
        >>> len(sample._context.items())
        5
        >>> sample._context['code']
        200
        """

        from testcase import TestResult

        log.debug('starting http sample')

        result = TestResult(self._name)
        if self.timeout:
            log.debug('setting request timeout')
            socket.setdefaulttimeout(self.timeout)

        # 开始采样了，开cookies，发送请求，获得响应结果，响应头。
        handlers = []
        # 如果允许Cookies，使用Cookies处理器
        if self._parent.cookies_enable:
            log.debug('enable cookies')
            handlers.append(urllib2.HTTPCookieProcessor())

        log.debug('building url opener')
        opener = urllib2.build_opener(*handlers)


        # 如果显式设置请求头
        if getattr(self,'headers',None):
            log.debug('setting headers')
            opener.addheaders = [(item.name,getattr(item,'value',None) or item._text) for item in self.headers.item]

        # 整理URL及参数
        log.debug('the url is %s'%self.url)
        url = self.url
        data = getattr(self,'data','')
        if data:
            data = urllib.urlencode(data.kwargs)

        if self.method.lower() == 'get':
            if data:
                url = '?'.join((url,data))
        try:
            log.debug('finnally , getting the url %s'%url)

            result.start_time = datetime.now()
            if data:
                response = opener.open(url,data)
            else:
                response = opener.open(url)
            result.end_time = datetime.now()

            # 采样的结果需要暴露5样东西：url,code，msg，responseText,responseHeaders
            
            result.url = self._parent._context[self.id+'.url'] = self._context['url'] = response.geturl()
            result.code = self._parent._context[self.id+'.code'] = self._context['code'] = response.code
            result.msg = self._parent._context[self.id+'.msg'] = self._context['msg'] = response.msg
            result.responseText = self._parent._context[self.id+'.responseText'] = self._context['responseText'] = response.read()
            result.responseHeaders = self._parent._context[self.id+'.responseHeaders'] = self._context['responseHeaders'] = response.info()
        except:
            result.end_time = datetime.now()
            result._sample = self
            result.status = "ERROR"
            result.code = 503
            result.exc_info = log_exce('something wrong')
        result.httpHeader = opener.addheaders
        return result

register('http',HTTPSampler)

class SOAPSampler(object):

    def is_valid(self):
        pass

    #校验并构造soap所需要的参数
    def setObj(self,kw,item,name,o=None,sign=None,k='',l=[]):
        
        if item.attributes.has_key('name') and item.attributes.has_key('type') and kw.has_key(item.attributes['name']):
            if item.attributes['type'][0] == self._namespace: 
                k += item.attributes['name']+'.'
                obj = argObj()
                d = kw[item.attributes['name']]
                if o == None:
                    kw[item.attributes['name']] = obj
                    
                else:
                    o._addItem(item.attributes['name'], obj)
                self.translate_arg(d,item.attributes['type'][1],obj,'',k,l)
            elif Types.bodyType in o.__class__.__bases__:
                o._addItem('ns1:'+item.attributes['name'],convert(kw[item.attributes['name']],item.attributes['type'][1]))
           
        else: 
            if item.attributes.has_key('name') and (not kw.has_key(item.attributes['name'])):
                if 'the args is required but not given,as follow:' in l:
                    l.append(k+item.attributes['name'])
                else:
                    l.append('the args is required but not given,as follow:')
                    l.append(k+item.attributes['name'])

    def getTypes(self,name,sign=None):
        if sign is None:
            te = self._wsdltypes.elements[name]
        else:
            te = self._wsdltypes.types[name]
        if te.attributes.has_key('type'):#java环境
            if te.attributes['type'][0] == self._namespace:
                te = self.getTypes(te.attributes['type'][1],'')
        elif getattr(te,'content',None):#c#环境
            while te.__class__ not in [tuple,list] and te is not None:
                te=getattr(te,'content',None)
        return te

    def translate_arg(self,kw,name,o=None,sign=None,k='',l=[]):
        te = self.getTypes(name,sign)
        if te is None or te.__class__ not in [tuple,list]: return False
        tel,kwl = len(te),len(kw.keys())
        attrlist = []
        #obj = argObj()
        for item in te:
            if tel == kwl:
                print '   |_attr name:'.ljust(10),item.attributes['name'].ljust(10),'type:'.ljust(10),item.attributes['type'][1] 
                self.setObj(kw,item,name,o,'',k,l)
            elif tel > kwl:
                l.append('the args given less than required,as follow:')
                if item.attributes.has_key('name') and (not kw.has_key(item.attributes['name'])):
                    l.append(k[:-1]+item.attributes['name'])
                break
            else:
                if item.attributes.has_key('name'):
                    attrlist.append(item.attributes['name'])
                break
        if len(attrlist) > 0:
            l.append('the args given more than required,as follow:')
            for (k1,v) in kw.items():
                if k1 not in attrlist:
                    l.append(k+k1)
        if len(l) >0 :return l
        else: return kw 
                   
   
    #把配置文件中的data转换成对应的json	
    def wrapdata(self):
        if self.data.format == 'json':
            import json
            if '\'' in self.data._text:
                self.data._text=self.data._text.replace('\'','\"')
            if self.data._text.__class__ in (str,unicode) and len(self.data._text)>0:
                self.data.kwargs=json.loads(self.data._text)
       
         
    # 采样的逻辑
    def sample(self):
        from testcase import TestResult
        result = TestResult(self._name)
        try:
            self.wrapdata()
            server = WSDL.Proxy(self.wsdl)
            self._namespace = namespace = server.wsdl.targetNamespace
            #设置argObj._validURI值
            argObj._validURIs = (namespace, )
            server.methods[self.method].namespace = namespace
            method = getattr(server,self.method)
            print '============soap method==============='
            print self.method
            print '============soap method==============='
            self._wsdltypes = server.wsdl.types[namespace]
            server.soapproxy.config.dumpSOAPOut = 1
            server.soapproxy.config.dumpSOAPIn = 1
            result.start_time = datetime.now()
           
            if self.data.kwargs:
                obj = argObj()
                
                kwargs = self.translate_arg(self.data.kwargs,self.method,obj)
                if kwargs.__class__ is dict:
                    print 'kwargs: ',kwargs
                    #obj._name =''
                    print 'obj:',obj.__dict__
                    #soap_result = method(**kwargs)

                    soap_result = method(obj)
                elif kwargs.__class__ is list:
                    print 'method\'s arg error!!!!'
                    error_root='the data._text of the SOAPsample named \''+self.id+'\' in '+self._parent.name+'.xml is error!!!'
                    errormsg=kwargs[0];
                    for item in kwargs[1:]:
                        errormsg+=item+';'
                    raise argsException,error_root+'\n\t\t\t'+errormsg
            else:
                soap_result = method()
            result.end_time = datetime.now()
            rs=self.getDataField(soap_result)
            result.soapRespone=self._parent._context[self.id] = self._context[self.id] = rs
            result.code =200
           
            if server.soapproxy.__dict__.has_key('soapmessage') and server.soapproxy.__dict__.has_key('soaprespone'):
                result.outcoming = server.soapproxy.__dict__['soapmessage']
                result.incoming = server.soapproxy.__dict__['soaprespone']
            
        except:
            result.start_time = datetime.now()
            result.end_time = datetime.now()
            result._sample = self
            result.status='ERROR'
            result.exc_info = log_exce('something wrong')
        
        return result
	   
    def getDataField(self,arg):
        if arg.__class__ == Types.structType:
            for item in arg.__dict__.items():
                if 'element' == item[0]: continue
                if '_'in item[0] : continue
                if 'schema' == item[0]: continue
                if item[1].__class__ is Types.structType:
                    arg = self.getDataField(item[1])
                elif type(item[1]) in (tuple,list):
                    arg = item[1]     
        return arg         
    
register('soap',SOAPSampler)

#ping类型处理器
class PINGSampler(object):
    def sample(self):
        #pass
        #import os
        from testcase import TestResult
        result = TestResult(self._name)
        result.status = None
        try:
            listForPipe = []
            command = self.commandForOs()
            result.start_time = datetime.now()
            respone = os.popen(command,'r')
            result.end_time = datetime.now()
            for item in respone.readlines():
                if item not in ['\r\n','\n'] and item not in listForPipe:
                    listForPipe.append(item)
                if result.status is None:
                    if 'loss' in item:
                        if self.getReply(item) <100:result.status = 'SUCCESS'
                        else: 
                            result.status = 'FAIL'
                            #result.exc_info = log_exce('can\'t connection')

        except:

            result.start_time = datetime.now()
            result.end_time = datetime.now()
            result._sample = self
            result.status='ERROR'
            result.exc_info = log_exce('something wrong')
        
        return result

    def getReply(self,item):
        r = re.search(r'[0-9]{1,3}[.]?[0-9]?%',item)
        percent = r.group(0)
        if len(percent)>0:
            percent = percent[:-1]
        try:
            percent = float(percent)
            return percent
        except:
            return 0
        
    def slice_http(self,ip):
        if '/' in ip:
            ip = ip[ip.rfind('/')+1:]
        else:ip = verify_ip(ip)
        print 'ip: ',ip
        return ip

    def pingwhat(self):
        if getattr(self,'ip',None):
            return self.slice_http(self.ip)
        elif getattr(self,'url',None):
            return self.slice_http(self.url)
        else:raise

    def commandForOs(self):
        if self.timeout:
            self.timeout = 30
        if os.name in ['nt']:
            command = 'ping %s'%self.pingwhat()
        elif os.name in ['posix']:
            command = 'ping -c 30 %s'%self.pingwhat() 
        return command
            
register('ping',PINGSampler)

#telnet处理器
class TELNETSampler(object):
    def sample(self):
        from testcase import TestResult
        from telnetlib import Telnet
        result = TestResult(self._name)
        try:
            self.sethost()
            result.start_time = datetime.now()
            t = Telnet(host=self.host,timeout = self.timeout)
            result.end_time = datetime.now()
            #t.close()
            result.status = 'SUCCESS'

        except:
            result.start_time = datetime.now()
            result.end_time = datetime.now()
            result._sample = self
            result.status='ERROR'
            result.exc_info = log_exce('something wrong')
        return result
        

    def sethost(self):
        if not getattr(self,'host',None):
            if getattr(self,'ip',None):
                self.host = self.ip
            elif getattr(self,'url',None):
                self.host = self.url
            elif getattr(self,'hostname',None):
                self.host = self.hostname
            else:raise
            #    self.host = '127.0.0.1'
register('telnet',TELNETSampler)      
if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=True)

