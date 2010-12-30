#encoding=utf-8

class TestAssertionError(Exception):
    pass

asserter_map = {}

def register(name,asserter):
    asserter_map[name] = asserter

def unregister(name):
    del asserter_map[name]

def get_asserter(name):
    return asserter_map[name]

# ============ binary asserter definitions =============

def make_binary_asserter(name,op,error_msg=''):
    """
    parameters:
    name,name of the asserter
    op,operator
    error_msg,assertion error message
    """
    def do_assert(op,error_msg,*args):
        assert len(args) == 2
        try:
            assert eval('args[0] %s args[1]'%op)
        except AssertionError:
            raise TestAssertionError,error_msg

    func = lambda *args : do_assert(op,error_msg,*args)

    register(name,func)

binary_asserters = (
    ('eq','==',''),
    ('ne','!=',''),
    ('in','in',''),
    ('ni','not in',''),
    ('ge','>=',''),
    ('gt','>',''),
    ('le','<=',''),
    ('lt','<',''),
)

for name,op,error_msg in binary_asserters:
    make_binary_asserter(name,op,error_msg)

# =========== other asserter definitions ========

def is_null(*args):
    for value in args:
        try:
            assert value is None
        except AssertionError:
            raise TestAssertionError,''

register('null',is_null)


def not_null(*args):
    for value in args:
        try:
            assert value is not None
        except AssertionError:
            raise TestAssertionError,''

register('nnull',not_null)

if __name__ == '__main__':
    print asserter_map
    print 'testing asserters'
    get_asserter('eq')(1,1)
    get_asserter('ne')(1,2)
    get_asserter('in')(1,[1,2])
    get_asserter('ni')(3,[1,2])
    get_asserter('ge')(2,1)
    get_asserter('ge')(1,1)
    get_asserter('gt')(2,1)
    get_asserter('le')(1,2)
    get_asserter('le')(1,1)
    get_asserter('lt')(1,2)
    get_asserter('null')(None)
    get_asserter('nnull')(1,2)
    try:
        get_asserter('nnull')(None)
    except TestAssertionError:
        print 'not null assertion error!'

    print 'all test past'
