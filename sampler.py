#encoding=utf-8

sampler_map = {}

def register(name,sampler):
  sampler_map[name] = sampler

def unregister(name):
  del sampler_map[name]

def get_sampler(name):
  return sampler_map[name]

class HTTPSampler:
  pass

register('http',HTTPSampler)

class SOAPSampler:
  pass

register('soap',SOAPSampler)
