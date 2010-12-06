#encoding=utf-8
from logger import log
from xml.dom import minidom

def get_child_tags(xml,tag=None):
    log.debug('getting child tags')
    ret = []
    for node in xml.childNodes:
        if node.__class__ == minidom.Element:
            if not tag:
                ret.append(node)
            elif node.tagName == tag:
                ret.append(node)
    return ret
