#!/usr/bin/python3

from itertools import zip_longest
from functools import partial, wraps
import operator
import inspect


_DUNDER = {
        'unary': ('__abs__', '__del__', '__delete__', '__float__', '__hash__', '__hex__', '__int__', '__invert__', '__neg__', '__oct__', '__nonzero__', '__repr__', '__reversed__', '__set__', '__str__', '__unicode__'),
        'binary': ('__add__', '__and__', '__cmp__', '__coerce__', '__complex__', '__contains__', '__delitem__', '__delslice__', '__div__', '__divmod__', '__eq__', '__floordiv__', '__ge__', '__get__', '__getitem__', '__getslice__', '__gt__', '__iadd__', '__iand__', '__idiv__', '__ifloordiv__', '__ilshift__', '__imod__', '__imul__', '__index__', '__ior__', '__ipow__', '__irshift__', '__isub__', '__itruediv__', '__ixor__', '__le__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__', '__or__', '__pos__', '__pow__', '__radd__', '__rand__', '__rcmp__', '__rdiv__', '__rdivmod__', '__rfloordiv__', '__rlshift__', '__rmod__', '__rmul__', '__ror__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__', '__rtruediv__', '__rxor__', '__setitem__', '__setslice__', '__sub__', '__truediv__', '__xor__'),
        'other': ('__iter__', '__slots__', '__weakref__')
        }


DEFAULT_MODE = "flat"


class Neq():
    def __eq__(self, other):
        return False


def zip_equal(*iterables):
    sentinel=Neq()
    return zip_longest(*iterables, fillvalue=sentinel)


def multo_len(m):
    return len(m.multo)


def inner_len(m):
    return m.multo_inner_len()

def inner_bool(m):
    return m.multo_inner_bool()

def inner_int(m):
    return m.multo_inner_int()

def inner_bytes(m):
    return m.multo_inner_bytes()

def inner_complex(m):
    return m.multo_inner_complex()


def multo(*args, **kwargs):

    if len(args) == 1 and _is_method(args[0]):
        assert not kwargs
        mode = args[0]
        return multo_decor(mode)

    elif not args and "mode" in kwargs:
        mode = kwargs.pop("mode", None)
        assert not kwargs
        return multo_decor(mode)

    else:
        return multo_list(*args, **kwargs)


def multo_decor(*args, mode=None):
    '''
    Usage:

    @multo_decor
    def abc():
        ...

    @multo_decor('zip')
    def abc():
        ...

    @multo_decor(mode='zip')
    def abc():
        ...

    @multo
    def abc():
        ...

    @multo(mode='zip')
    def abc():
        ...
    '''

    if len(args) == 1 and callable(args[0]):
        f = args[0]

    elif len(args) == 0:
        # called as @multo_decor() maybe with mode kw
        return partial(multo_decor, mode=mode)

    elif len(args) == 1:
        # called as @multo_decor(mode)
        mode = args[0]
        return partial(multo_decor, mode=mode)

    else:
        raise ValueError("Invalid multo_decor arguments")

    if mode is not None:
        mode = mode[:4]
        if mode.startswith("zip"):
            mode = "zip"
        assert mode in ("flat", "nest", "zip")

    @wraps(f, updated=())
    def expander(*args, mode=None):

        if len(args) == 1:
            a = args[0]
            if isinstance(a, multo_list):
                return multo_list(multo=[expander(aa) for aa in a.multo])
            return f(a)

        # for setitem() there is an additional 3rd value item, must be passed around
        a, b, *c = args

        if isinstance(b, multo_list) and isinstance(a, multo_list):

            if not mode:
                if a.multo_mode is None and b.multo_mode is None:
                    mode = DEFAULT_MODE
                elif a.multo_mode is None:
                    mode = b.multo_mode
                elif b.multo_mode is None:
                    mode = a.multo_mode
                elif a.multo_mode == b.multo_mode:
                    mode = a.multo_mode
                else:
                    raise AttributeError(f"Incompatible multo types {a.multo_mode} and {b.multo_mode}")

            if   mode == "flat":
                return multo_list(multo=[expander(aa, bb, *c, mode=mode) for bb in b.multo for aa in a.multo])

            elif mode == "nest":
                pass

            elif mode == "zip":
                if multo_len(a) != multo_len(b):
                    raise IndexError("Non-equal length of zipped multos")
                return multo_list(multo=[expander(aa, bb, *c, mode=mode) for aa, bb in zip(a.multo, b.multo)])

        if isinstance(b, multo_list):
            return multo_list(multo=[expander(a, bb, *c, mode=mode) for bb in b.multo])

        if isinstance(a, multo_list):
            return multo_list(multo=[expander(aa, b, *c, mode=mode) for aa in a.multo])

        return f(a, b, *c)

    if len(args) == 1 and callable(args[0]):
        # called as @multo_decor
        return partial(expander, mode=mode)


def _is_method(elem):
    return inspect.ismethod(elem) or inspect.isfunction(elem)


class multo_list:

    __SUPER_METHODS = ("multo", "multo_mode")

    @property
    def multo(self):
        return self.__multo

    @multo.setter
    def multo(self, value):
        assert isinstance(value, list)
        self.__multo = value

    @property
    def multo_mode(self):
        return self.__mode

    @multo_mode.setter
    def multo_mode(self, value):
        self.__mode = value

    def __call__(self, *args, **kwargs):
        raise TypeError('Trying to call multo or invalid multo decorator use')

    def __init__(self, *args, **kwargs):

        if "multo" in kwargs:
            self.multo = kwargs.pop("multo")

        elif args:
            self.multo = list(args)

        self.multo_mode = kwargs.pop("mode", None)
        assert not kwargs

        self.__decor = multo_decor(mode=self.multo_mode)

    def __getattribute__(self, attr):

        if not attr.startswith("_multo_list__") and not attr.startswith("multo_inner_") and not attr in self.__SUPER_METHODS:
            raise AttributeError(f"Attribute {attr} not recognized")

        return super().__getattribute__(attr)

    def __getattr__(self, attr):

        itattr = None

        for item in self.multo:
            itattr = getattr(item, attr)
            break

        if _is_method(itattr):

            @wraps(itattr)
            def mulmethod(*args, **kwargs):
                return multo_list(*tuple(getattr(item, attr)(*args, **kwargs) for item in self.multo))

            return mulmethod

        return multo_list(*tuple(getattr(item, attr) for item in self.multo))

    def __eq__(self, other):
        if not isinstance(other, multo_list):
            return False
        return all(a == b for a, b in zip_equal(self.multo, other.multo))

    def __str__(self):
        return "~[ %s ]~" % ", ".join(str(item) for item in self.multo)

    def __repr__(self):
        return "multo(%s)" % ", ".join(repr(item) for item in self.multo)

    def __len__(self):
        '''
        It would be nice to let __len__ return a multo of inner item lengths,
        but len() must return an integer.
        Returns multo len.
        '''
        return len(self.multo)

    def __bool__(self):
        an = any(self.multo)
        al = all(self.multo)

        if an == al:
            return an

        raise(ValueError("Conversion to bool failed: not all multo values evaluate to the same bool"))

    def __complex__(self):
        raise AttributeError("Cannot use dunder method complex, use multo.inner_complex")

    def __int__(self):
        raise AttributeError("Cannot use dunder method int, use multo.inner_int")

    def __bytes__(self):
        raise AttributeError("Cannot use dunder method bytes, use multo.inner_bytes")

    def __index__(self):
        index_list = self.__unary_proxy(operator.index)

        if len(set(index_list.multo)) == 1:
            return index_list.multo[0]

        raise(ValueError("Conversion to index failed: not all multo values evaluate to the same index"))

    def __unary_proxy(self, op):
        return self.__decor(op)(self)

    def __neg__(self):
        return self.__unary_proxy(operator.neg)

    def __pos__(self):
        return self.__unary_proxy(operator.pos)

    def __abs__(self):
        return self.__unary_proxy(operator.abs)

    def __invert__(self):
        return self.__unary_proxy(operator.invert)

    def multo_inner_len(self):
        return self.__unary_proxy(len)

    def multo_inner_bool(self):
        return self.__unary_proxy(bool)

    def multo_inner_int(self):
        return self.__unary_proxy(int)

    def multo_inner_bytes(self):
        return self.__unary_proxy(bytes)

    def multo_inner_complex(self):
        return self.__unary_proxy(complex)

    #'unary': ('__del__', '__delete__', '__float__', '__hash__', '__hex__', '__int__', '__oct__', '__nonzero__', '__reversed__', '__str__', '__unicode__'),

    def __binary_proxy(self, other, op):
        return self.__decor(op)(self, other)

    def __add__(self, other):
        return self.__binary_proxy(other, operator.add)

    def __radd__(self, other):
        return self.__binary_proxy(other, lambda x, y: y+x)

    def __sub__(self, other):
        return self.__binary_proxy(other, operator.sub)

    def __rsub__(self, other):
        return self.__binary_proxy(other, lambda x, y: y-x)

    def __mul__(self, other):
        return self.__binary_proxy(other, operator.mul)

    def __rmul__(self, other):
        return self.__binary_proxy(other, lambda x, y: y*x)

    def __truediv__(self, other):
        return self.__binary_proxy(other, operator.truediv)
    
    def __rtruediv__(self, other):
        return self.__binary_proxy(other, lambda x, y: y/x)

    def __floordiv__(self, other):
        return self.__binary_proxy(other, operator.floordiv)
    
    def __rfloordiv__(self, other):
        return self.__binary_proxy(other, lambda x, y: y//x)

    def __mod__(self, other):
        return self.__binary_proxy(other, operator.mod)

    def __rmod__(self, other):
        return self.__binary_proxy(other, lambda x, y: y%x)

    def __divmod__(self, other):
        return self.__binary_proxy(other, lambda x, y: divmod(x, y))

    def __rdivmod__(self, other):
        return self.__binary_proxy(other, lambda x, y: divmod(y, x))

    def __pow__(self, other):
        return self.__binary_proxy(other, operator.pow)

    def __rpow__(self, other):
        return self.__binary_proxy(other, lambda x, y: y**x)

    def __and__(self, other):
        return self.__binary_proxy(other, operator.and_)

    def __rand__(self, other):
        return self.__binary_proxy(other, lambda x, y: y&x)

    def __or__(self, other):
        return self.__binary_proxy(other, operator.or_)

    def __ror__(self, other):
        return self.__binary_proxy(other, lambda x, y: y|x)

    def __xor__(self, other):
        return self.__binary_proxy(other, operator.xor)

    def __rxor__(self, other):
        return self.__binary_proxy(other, lambda x, y: y^x)

    def __lshift__(self, other):
        return self.__binary_proxy(other, operator.lshift)

    def __rlshift__(self, other):
        return self.__binary_proxy(other, lambda x, y: y<<x)

    def __rshift__(self, other):
        return self.__binary_proxy(other, operator.rshift)

    def __rrshift__(self, other):
        return self.__binary_proxy(other, lambda x, y: y>>x)

    def __lt__(self, other):
        return self.__binary_proxy(other, operator.lt)

    def __le__(self, other):
        return self.__binary_proxy(other, operator.le)

    def x__eq__(self, other):
        #TODO
        return self.__binary_proxy(other, operator.eq)

    def x__ne__(self, other):
        #TODO
        return self.__binary_proxy(other, operator.ne)

    def __ge__(self, other):
        return self.__binary_proxy(other, operator.ge)

    def __gt__(self, other):
        return self.__binary_proxy(other, operator.gt)

    def __contains__(self, other):
        return self.__binary_proxy(other, operator.contains)

    def __getitem__(self, other):
        return self.__binary_proxy(other, operator.getitem)

    def __ternary_proxy(self, other, op, value):
        return self.__decor(op)(self, other, value)

    def __setitem__(self, index, value):
        return self.__ternary_proxy(index, operator.setitem, value)

    def __delitem__(self, other):
        return self.__binary_proxy(other, operator.delitem)

    def __delslice__(self, other):
        return self.__binary_proxy(other, operator.delslice)

    def __getslice__(self, other):
        return self.__binary_proxy(other, operator.getslice)

    def __setslice__(self, other):
        return self.__binary_proxy(other, operator.setslice)

    def __iadd__(self, other):
        return self.__binary_proxy(other, operator.iadd)

    def __isub__(self, other):
        return self.__binary_proxy(other, operator.isub)

    def __imul__(self, other):
        return self.__binary_proxy(other, operator.imul)

    def __itruediv__(self, other):
        return self.__binary_proxy(other, operator.itruediv)

    def __ifloordiv__(self, other):
        return self.__binary_proxy(other, operator.ifloordiv)

    def __ilshift__(self, other):
        return self.__binary_proxy(other, operator.ilshift)

    def __imod__(self, other):
        return self.__binary_proxy(other, operator.imod)

    def __iand__(self, other):
        return self.__binary_proxy(other, operator.iand)

    def __ior__(self, other):
        return self.__binary_proxy(other, operator.ior)

    def __ipow__(self, other):
        return self.__binary_proxy(other, operator.ipow)

    def __irshift__(self, other):
        return self.__binary_proxy(other, operator.irshift)

    def __ixor__(self, other):
       return self.__binary_proxy(other, operator.ixor)

    def x__hash__(self):
        #TODO
        raise

    def x__format__(self, format_spec):
        #TODO
        raise

def _gen_dunder():
    for op in _DUNDER['binary']:
        print(f'    def {op}(self, other):\n        return self.__binary_proxy(other, operator.{op[2:-2]})\n')
