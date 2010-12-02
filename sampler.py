#encoding=utf-8

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
	pass

register('http',HTTPSampler)

class SOAPSampler(object):

  def is_valid(self):
	pass

  # 采样的逻辑
  def sample(self):
	pass

register('soap',SOAPSampler)
