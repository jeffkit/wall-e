#encoding=utf-8

assertser_map = {}

def register(name,assertser):
  assertser_map[name] = assertser

def unregister(name):
  del assertser_map[name]

def get_assertser(name):
  return assertser_map[name]

# ============ assertser definitions =============

def assert_eq(*args):
  pass

register('eq',assert_eq)



