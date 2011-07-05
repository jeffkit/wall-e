#encoding=utf-8
import traceback
import sys
from xml.dom import minidom
from logger import log,log_exce
import testcase
sampletype ={}
def init_sampletype():
    sampletype['HTTP'] = 'url'
    sampletype['SOAP'] = 'wsdl'
    sampletype['FTP'] = 'ftp'
    sampletype['PING'] = 'url'
    sampletype['TELNET'] = 'url'

init_sampletype()

def create_xml_doc():
    return  minidom.Document()

def xml_head(result,xml_doc):
    testResult = xml_doc.createElement("testResult")
    testResult.setAttribute("name",result.testcase.name)
    testResult.setAttribute("status",result.status)
    testResult.setAttribute("start_time",str(result.start_time))
    testResult.setAttribute("end_time",str(result.end_time))
    testResult.setAttribute("time_used",str(result.end_time-result.start_time))
    xml_doc.appendChild(testResult)
    return testResult

def xml_body(result,headnode):pass

def xml_sample(result,headnode,xml_doc):
    child = xml_doc.createElement(result.nodetype)
    child.setAttribute('id',result._sample.id)
    if getattr(result._sample,'url',None):
        child.setAttribute('url',result._sample.url)
    if getattr(result._sample,'wsdl',None):
        child.setAttribute('wsdl',result._sample.wsdl)
    child.setAttribute('method',result._sample.method)
    if getattr(result,'code',None):
        child.setAttribute('code',str(result.code))
    child.setAttribute('status',result.status)
    child.setAttribute('start_time',str(result.start_time))
    child.setAttribute('end_time',str(result.end_time))
    child.setAttribute('time_used',str(result.end_time-result.start_time))
    headnode.appendChild(child)
    return child
   
def xml_assert(result,headnode,xml_doc):
    child = xml_doc.createElement(result.nodetype)
    child.setAttribute('status',result.status)
    if result._assert.__dict__.has_key('type'):
        child.setAttribute('type',result._assert.type)
        if result._assert.__dict__.has_key('item'):
            args = [item._text for item in result._assert.item]
            exp = result._assert.type+'['
            for i in args:
                exp += str(i)+','
            exp = exp[:-1]+']'
            child.setAttribute('expression',exp)
    headnode.appendChild(child)
    return child

def xml_except(result,headnode,xml_doc):
    rs_except = xml_doc.createElement('exception')
    rs_except_text1 = xml_doc.createTextNode('ERROR: %s'%str(result.exc_info[0]).replace('<','').replace('>',''))
    rs_except.appendChild(rs_except_text1)
    rs_except_text2 = xml_doc.createTextNode('ERROR: %s'%result.exc_info[1].message)
    rs_except.appendChild(rs_except_text2)
    rs_except_textmsg = xml_doc.createTextNode('More Information:')
    rs_except.appendChild(rs_except_textmsg)
    for filename, lineno, function, msg in traceback.extract_tb(result.exc_info[2]):
        rs_except_text3 = xml_doc.createTextNode('%s line %s in %s function [%s]'%(filename,lineno,function,msg))
        rs_except.appendChild(rs_except_text3)
    headnode.appendChild(rs_except)

class MutiFormat(object):

    def getdumper(self,name):
        from dumper import get_dumper,getRegdumpers
        dumpers = getRegdumpers()
        if dumpers.has_key(name):
            dum = get_dumper(name)
        else:
            dum = get_dumper('DEFAULT')
        return dum()

    def weave(self):
        xml_doc = create_xml_doc()
        headnode = xml_head(self,xml_doc)
        for rs in self.sections:
            if rs.nodetype in [u'sample','sample']:
                child = xml_sample(rs,headnode,xml_doc)
                if getattr(rs,'log',None):
		            #self.getdumpler(rs)
                    try:
                        demper = self.getdumper(rs._sample.type.upper())
                        demper.dump(rs,headnode,xml_doc) 
                    except:
                        log.debug('have no dumper about  %s sampler'%rs._sample.type)
                        for filename, lineno, function, msg in traceback.extract_tb(sys.exc_info()[2]):
                            print '%s line %s in %s function [%s]'%(filename,lineno,function,msg)
                
                #if rs.status in ['ERROR','FAIL']:
                if getattr(rs,'exc_info',None):
                    xml_except(rs,child,xml_doc)
            else:
                xml_assert(rs,headnode,xml_doc)
        if self.__dict__.has_key('exc_info'):
            xml_except(self,headnode,xml_doc)
        return xml_doc
    
    def toxml(self):
        return self.weave()

    def appendHtmlHead(self):
        params = (self.testcase.name,self.testcase.timeout,self.testcase.loop,self.testcase.frequency)
        headtable =u'''\
        拨测案例信息头:<br>
        <table width = '800px' class='Tab'>
            <tr>
                <td>案例名称</td>
                <td>休息时间</td>
                <td>循环次数</td>
                <td>频率</td>
            </tr>
            <tr>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
            </tr>
        </table>
        '''%params
        return headtable

    def appendHtmlDetail(self):
        dtable = u'''\
        拨测案例结果及相关信息:<br>
        <table width = '800px' class='Tab'>
            <tr>
                <td width='8%'>采样/断言</td>
                <td width='8%'>id</td>
                <td width='8%'>类型</td>
                <td width='20%'>相应的url</td>
                <td width='8%'>方法</td>
                <td width='8%'>休息时间</td>
                <td width='10%'>开始时间</td>
                <td width='10%'>结束时间</td>
                <td width='10%'>所用时间</td>
                <td width='8%'>状态</td>
            </tr>
        '''
        childlist = self.testcase._children
        rslist = self.sections
        for i in range(len(childlist)):
            childstr = ''
            bgcolor = ''
            params = ()
            if i ==len(self.sections)-1:
                bgcolor ='red'
            if i <= len(self.sections)-1:
                if getattr(rslist[i],'start_time',None) and getattr(rslist[i],'end_time',None):
                    params += (str(rslist[i].start_time)[:-7],)
                    params += (str(rslist[i].end_time)[:-7],)
                    params += (str((rslist[i].end_time-rslist[i].start_time).microseconds)+'ms',)
                else:params += ('--','--','--')
                params += (rslist[i].status,)
            else:
                params += ('--','--','--','--')
          
            if childlist[i].__class__ is testcase.Assert:
                aparams = (bgcolor,childlist[i].type)
                try:
                    args = [item._text for item in childlist[i].item]
                except:
                    args =['--','--']
                for it in args:
                    aparams += (it,)
                aparams += params
                childstr +='''\
                <tr bgcolor='%s'>
                    <td>assert</td>
                    <td colspan='5'>expression="%s[%s,%s]"</td>
                    <td >%s</td>
                    <td >%s</td>
                    <td >%s</td>
                    <td >%s</td>
                    </tr>
                '''%aparams
            else:
                url = getattr(childlist[i],sampletype[childlist[i].type],'--')
                sparams = (bgcolor,childlist[i].id,childlist[i].type,url,childlist[i].method,childlist[i].timeout)
                sparams += params   
                childstr +='''\
                <tr bgcolor='%s'>
                    <td>sample</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>
                '''%sparams
            dtable += childstr
        dtable +='</table>'
       
        return dtable
    
    def appendHtmlexcept(self):
        content = u'<div>'
        content += u'案例异常信息如下:<br>'
        exceptlist = [] 
        if getattr(self,'exc_info',None):
            exceptlist.append(self.exc_info)
        if  getattr(self.sections[-1:][0],'exc_info',None):
            exceptlist.append(self.sections[-1:][0].exc_info)
        for item in exceptlist:
            content += str(item[0])
            content += item[1].message
            content += u'更多异常信息....<BR>'
            for filename, lineno, function, msg in traceback.extract_tb(item[2]):
                content += '%s line %s in %s function [%s] <br>'%(filename,lineno,function,msg)
        '''
        else:
            rs = self.sections[-1:][0]
            content += str(rs.exc_info[0])
            content += rs.exc_info[1].message
            content += u'<br>更多异常信息....<BR>'
            if getattr(rs,'exc_info',None):
                 for filename, lineno, function, msg in traceback.extract_tb(rs.exc_info[2]):
                     content += '%s line %s in %s function [%s] <br>'%(filename,lineno,function,msg)
        '''
        content += '</div>'
        #etable += content
        print 'content: ',content
        return content
        


    def tohtml(self): 
        html = u'''\
                <html><head>
                <style type="text/css">
                    .Tab{ border-collapse:collapse;}
                    .Tab td{ border:solid 1px black}
                </style>
                </head><body>
        '''
        text = u'你好,最新的一次拨测错误结果如下<br>'
        html += text
        html += u'更多的详细信息:<br>'
        html += self.appendHtmlHead()
        html += self.appendHtmlDetail()
        html += self.appendHtmlexcept()
        html += '</body></html>'
        return html
        

'''
    def toArgsTuple(self,rs):
        params = ()
        if getattr(rs,'nodetype',None):    
            params += (rs.testcase.name,)
            params += (rs.status,)
            params += (rs.start_time.__str__()[:-3],)
            params += (rs.end_time.__str__()[:-3],)
            
        elif getattr(rs,'nodetype',None) in [u'sample','sample']:
           
            params += (rs._sample.id,)
            params += (rs._sample.type,)
            params += (rs._sample.method,)
            params += (rs._sample.timeout,)
            if rs.log:params += (1,)
            else:params += (0,)
            params += (rs.start_time.__str__()[:-3],)
            params += (rs.end_time.__str__()[:-3],)
            params += (rs.status,)
        elif getattr(rs,'nodetype',None) in [u'assert','assert']:
            params += (rs._assert.type,)
            params += (rs.status,)
            params += (int(test_id),)

        return params
'''