#encoding=utf-8
from logger import log,log_exce
from config import Config
#from result2xml import build
import os
import sys
class resultHander:
    def handle(self,result=None):
        pass

class xmlHandler(resultHander):
    def __init__(self,config=Config):
        log.debug('handle result in your way!xmlHandler')
        self.config = config

    def handle(self,result):
        self.result_xml(result)

    def get_testResult_dir(self):
        rsdir = self.config.test_result_dir
        if not os.path.exists(rsdir):
            rsdir = os.path.sep.join((os.getcwd(),rsdir))
            if not os.path.exists(rsdir):
	            try:
	                os.makedirs(rsdir)
	            except:
	                rsdir = os.path.sep.join((os.getcwd(),'result'))
                    os.makedirs(rsdir)
        return os.path.abspath(rsdir)

    def result_xml(self,result):
        log.debug('save test result to xml ')
        rsdir = self.get_testResult_dir()
        '''
        xml_builder = build(result)
        xml_doc = xml_builder.get_xml_doc()
        '''
        xml_doc = result.toxml()
        filename = str(result.end_time).replace(' ','_').replace(':','_')
        filename = filename+'.xml'
        filename = result.testcase.name+'_'+filename
        filename = os.path.sep.join((rsdir,filename))
        f = file(filename,'w')
        import codecs
        writer = codecs.lookup('utf-8')[3](f)
        xml_doc.writexml(writer,'','    ','\n', encoding='utf-8')
        writer.close()

class multResultHandler(resultHander):

    def __init__(self,handlelist=None):
        log.debug('handle result in your way!==multResultHandler')
        self.handles =[]
        try:
            for item in handlelist:
                self.addResultHandler(item)
        except:
            log.error('handle result error!! ')

    def handle(self,result=None):
        for item in self.handles:
            if item.__class__ is not self.__class__:
                item.handle(result)
    def addResultHandler(self,rh):
        if resultHander in rh.__class__.__bases__:
            self.handles.append(rh)

