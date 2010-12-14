#encoding=utf-8
import urllib
import urllib2
import socket
from SOAPpy import WSDL
from logger import log,log_exce

sampler_map = {}

def register(name,sampler):
    sampler_map[name] = sampler

def unregister(name):
    del sampler_map[name]

def get_sampler(name):
    return sampler_map[name]

# ============ Sampler定义，这些类均不应直接实例化，是被Mixin到Sample类里面使用的 ============

class HTTPSampler(object):

    # 在此判断所需要的信息是否完整
    def is_valid(self):
        pass

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
        >>> sample.data = data
        >>> sample.url
        'http://www.botwave.com'
        >>> sample()
        >>> len(sample._context.items())
        5
        >>> sample._context['code']
        200
        """
        if self.timeout:
            socket.setdefaulttimeout(self.timeout)

        # 开始采样了，开cookies，发送请求，获得响应结果，响应头。
        handlers = []

        # 如果允许Cookies，使用Cookies处理器
        if self._parent.cookies_enable:
            handlers.append(urllib2.HTTPCookieProcessor())

        opener = urllib2.build_opener(*handlers)

        # 如果显式设置请求头
        if getattr(self,'headers',None):
            opener.addheaders = [(item.name,getattr(item,'value',None) or item._text) for item in self.headers.item]

        # 整理URL及参数
        url = self.url
        log.debug('the url is %s'%url)
        data = getattr(self,'data','')
        if data:
            data = urllib.urlencode(data.kwargs)

        if self.method.lower() == 'get':
            if data:
                url = '?'.join((url,data))
        try:
            log.debug('finnally , getting the url %s'%url)
            if data:
                response = opener.open(url,data)
            else:
                response = opener.open(url)
            # 采样的结果需要暴露5样东西：url,code，msg，responseText,responseHeaders
            self._context['url'] = response.geturl()
            self._context['code'] = response.code
            self._context['msg'] = response.msg
            self._context['responseText'] = response.read()
            self._context['responseHeaders'] = response.info()
        except:
            log_exce('something wrong')
            # 在这里处理异常


register('http',HTTPSampler)

class SOAPSampler(object):

    def is_valid(self):
        pass

    def translate_arg(self,kw):
        # 把字典转译成SOAPpy能懂的类型
        pass

    # 采样的逻辑
    def sample(self):
        server = WSDL.Proxy(self.wsdl)
        namespace = server.wsdl.targetNamespace
        server.methods[self.method].namespace = namespace
        method = getattr(server,self.method)
        if self.data.kwargs:
            kwargs = self.translate_arg(self.data.kwargs)
            result = method(**kwargs)
        else:
            result = method()




register('soap',SOAPSampler)

if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=True)

