#!/usr/bin/python3

from pytest import raises

from multo import multo, multo_decor, multo_len, inner_len, inner_int, inner_bytes, inner_complex
M = multo


def test_multo_len():
    m = M(1, 2, 3)
    assert multo_len(m) == 3

def test_inner_len():
    m = M("a", "bb", "ccc")
    assert inner_len(m) == M(1, 2, 3)

def test_str():
    m = M(1, 2, 3)
    assert str(m)  == "~[ 1, 2, 3 ]~"

def test_repr():
    m = M(1, 2, 3)
    assert repr(m)  == "multo(1, 2, 3)"

def test_scalar():
    m = M(1, 2, 3)
    assert m*2 == M(2, 4, 6)

def test_custom_inc():
    a = 2
    aa = M(2, 3, 4)

    @multo
    def custom_inc(a):
        return a+1

    assert custom_inc(a) == 3
    assert custom_inc(aa) == M(3, 4, 5)

def test_decor_ways():
    a = 2
    aa = M(2, 3, 4)

    @multo_decor
    def custom_inc(a):
        return a+1

    assert custom_inc(a) == 3
    assert custom_inc(aa) == M(3, 4, 5)

    @multo_decor()
    def custom_inc(a):
        return a+1

    assert custom_inc(a) == 3
    assert custom_inc(aa) == M(3, 4, 5)

    @multo_decor('flat')
    def custom_inc(a):
        return a+1

    assert custom_inc(a) == 3
    assert custom_inc(aa) == M(3, 4, 5)

    @multo_decor(mode='flat')
    def custom_inc(a):
        return a+1

    assert custom_inc(a) == 3
    assert custom_inc(aa) == M(3, 4, 5)

    with raises(ValueError):
        @multo_decor('flat', 'nest')
        def custom_inc(a):
            return a+1

    def custom_inc(a):
        return a+1

    assert custom_inc(a) == 3
    assert custom_inc(aa) == M(3, 4, 5)

    @multo(mode='flat')
    def custom_inc(a):
        return a+1

    assert custom_inc(a) == 3
    assert custom_inc(aa) == M(3, 4, 5)

    with raises(TypeError):
        @multo('flat')
        def custom_inc(a):
            return a+1


def test_custom_multiply():

    @multo
    def custom_multiply(a, b):
        return a*b+1

    a = 2
    b = 3
    aa = M(2, 3, 4, 5)
    bb = M(multo=[2, 4, 6])

    assert custom_multiply(a , b ) == 7
    assert custom_multiply(aa, b ) == M(7, 10, 13, 16)
    assert custom_multiply(a , bb) == M(5, 9, 13)
    assert custom_multiply(aa, bb) == M(5, 7, 9, 11, 9, 13, 17, 21, 13, 19, 25, 31)


def test_custom_multiply_nest():

    @multo(mode="nest")
    def custom_multiply_nest(a, b):
        return a*b+1

    a = 2
    b = 3
    aa = M(2, 3, 4, 5)
    bb = M(multo=[2, 4, 6])

    assert custom_multiply_nest(a , b ) == 7
    assert custom_multiply_nest(aa, b ) == M(7, 10, 13, 16)
    assert custom_multiply_nest(a , bb) == M(5, 9, 13)
    assert custom_multiply_nest(aa, bb) == M(M(5, 7, 9, 11), M(9, 13, 17, 21), M(13, 19, 25, 31))


def test_custom_multiply_zip():

    @multo(mode="zip")
    def custom_multiply_zip(a, b):
        return a*b+1

    a = 2
    b = 3
    aa = M(2, 3, 4, 5)
    bb = M(multo=[2, 4, 6, 8])
    cc = M(multo=[2, 4, 6])

    assert custom_multiply_zip(a , b ) == 7
    assert custom_multiply_zip(aa, b ) == M(7, 10, 13, 16)
    assert custom_multiply_zip(a , bb) == M(5, 9, 13, 17)
    assert custom_multiply_zip(aa, bb) == M(5, 13, 25, 41)

    with raises(IndexError):
        custom_multiply_zip(aa, cc)


def test_str():

    assert str (M("a1", "a2")) == "~[ a1, a2 ]~"
    assert repr(M("a1", "a2")) == "multo('a1', 'a2')"

    assert M("a1", "a2"             ) + M("b1", "b2"             ) == M("a1b1", "a2b1", "a1b2", "a2b2")
    assert M("a1", "a2", mode="flat") + M("b1", "b2"             ) == M("a1b1", "a2b1", "a1b2", "a2b2")
    assert M("a1", "a2", mode="flat") + M("b1", "b2", mode="flat") == M("a1b1", "a2b1", "a1b2", "a2b2")

    assert M("a1", "a2", mode="zip" ) + M("b1", "b2") == M("a1b1", "a2b2")
    assert M("a1", "a2", mode="nest") + M("b1", "b2") == M(M("a1b1", "a2b1"), M("a1b2", "a2b2"))


class strabc():

    def __init__(self, s="abc"):
        self._s = s

    def get_text(self):
        return self._s

    @property
    def text(self):
        return self._s

    def texttext(self):
        return self._s + self._s

    def append(self, s):
        self._s += s

    def appended(self, s):
        return self._s + s

    def prepended(self, s):
        return s + self._s

    def __str__(self):
        return self._s

    def __repr__(self):
        return "strabc(%s)" % repr(self._s)

    def __add__(self, other):
        return strabc(self.appended(str(other)))

    def __radd__(self, other):
        return strabc(self.prepended(str(other)))

    def __eq__(self, other):
        return isinstance(other, strabc) and self.text == other.text


def test_cls():

    aa = M(strabc(), strabc(""), strabc("x"))

    assert str(aa)   == "~[ abc, , x ]~"
    assert repr(aa)  == "multo(strabc('abc'), strabc(''), strabc('x'))"
    assert aa.get_text() == M('abc', '', 'x')
    assert aa.text   == M('abc', '', 'x')
    assert aa.texttext() == M('abcabc', '', 'xx')
    assert aa.appended('def') == M('abcdef', 'def', 'xdef')
    aa.append('z')
    assert aa.text == M('abcz', 'z', 'xz')

    bb = M(M(strabc()))
    assert bb.text == M(M('abc'))


def test_cls_with_str():

    aa = M(strabc(), strabc(""), strabc("x"))

    b = 'h'
    aab = aa + b
    assert aab.get_text() == M('abch', 'h', 'xh')
    assert aab.text == M('abch', 'h', 'xh')
    assert aab == M(strabc('abch'), strabc('h'), strabc('xh'))

    baa = b + aa
    assert baa.get_text() == M('habc', 'h', 'hx')
    assert baa.text == M('habc', 'h', 'hx')
    assert baa == M(strabc('habc'), strabc('h'), strabc('hx'))

    with raises(TypeError):
        aab = aa * b

    with raises(TypeError):
        baa = b * aa

def test_cls_with_cls():

    aa = M(strabc(), strabc(""), strabc("x"))

    bb = M(strabc('a'), strabc('b'), strabc('c'))
    aabb = aa + bb
    assert aabb.text == M('abca', 'a', 'xa', 'abcb', 'b', 'xb', 'abcc', 'c', 'xc')

    bb = M(strabc('a'), strabc('b'), strabc('c'), mode='zip')
    aabb = aa + bb
    assert aabb.text == M('abca', 'b', 'xc')

    bb = M(strabc('a'), strabc('b'), strabc('c'), mode='nest')
    aabb = aa + bb
    assert aabb.get_text() == M(M('abca', 'a', 'xa'), M('abcb', 'b', 'xb'), M('abcc', 'c', 'xc'))
    assert aabb.text == M(M('abca', 'a', 'xa'), M('abcb', 'b', 'xb'), M('abcc', 'c', 'xc'))

def test_dunder():

    a = M(2)

    assert a + 3 == M(2 + 3)
    assert 3 + a == M(3 + 2)
    assert a - 3 == M(2 - 3)
    assert 3 - a == M(3 - 2)
    assert a * 3 == M(2 * 3)
    assert 3 * a == M(3 * 2)
    assert a / 3 == M(2 / 3)
    assert 3 / a == M(3 / 2)
    assert a // 3 == M(2 // 3)
    assert 3 // a == M(3 // 2)
    assert a % 3 == M(2 % 3)
    assert 3 % a == M(3 % 2)

    assert divmod(a, 3) == M(divmod(2, 3))
    assert divmod(3, a) == M(divmod(3, 2))

    assert a ** 3 == M(2 ** 3)
    assert 3 ** a == M(3 ** 2)

    assert a & 6 == M(2 & 6)
    assert 6 & a == M(6 & 2)
    assert a | 6 == M(2 | 6)
    assert 6 | a == M(6 | 2)
    assert a ^ 6 == M(2 ^ 6)
    assert 6 ^ a == M(6 ^ 2)

    assert ~a == M(~2)

    assert a >> 3 == M(2 >> 3)
    assert 3 >> a == M(3 >> 2)
    assert a << 3 == M(2 << 3)
    assert 3 << a == M(3 << 2)

    assert -a == M(-2)
    assert +a == M(+2)
    assert abs(a) == M(abs(2))

    assert inner_complex(a) == M(complex(2))
    assert inner_int(a) == M(int(2))
    assert inner_bytes(a) == M(bytes(2))

    assert not a <  1
    assert not a <  2
    assert     a <  3
    assert not a <= 1
    assert     a <= 2
    assert     a <= 3
    assert     a >= 1
    assert     a >= 2
    assert not a >= 3
    assert     a >  1
    assert not a >  2
    assert not a >  3

    assert not 1 >  a
    assert not 2 >  a
    assert     3 >  a
    assert not 1 >= a
    assert     2 >= a
    assert     3 >= a
    assert     1 <= a
    assert     2 <= a
    assert not 3 <= a
    assert     1 <  a
    assert not 2 <  a
    assert not 3 <  a

    if False:
        assert not a == 1
        assert     a == 2
        assert not a == 3
        assert     a != 1
        assert not a != 2
        assert     a != 3
        assert not 1 == a
        assert     2 == a
        assert not 3 == a
        assert     1 != a
        assert not 2 != a
        assert     3 != a

    a = M(True)
    assert a
    assert (a and False) == False
    assert (a or  False) == a
    a = M(False)
    assert not a
    assert (a and False) == a
    assert (a or  False) == False

    a = M('abc')
    assert 'a' in a
    assert 'z' not in a
    assert a[1] == M('b')

    a = M([1, 2, 3])
    assert a[1] == M(2)
    a[1] = 4
    assert a == M([1, 4, 3])
    del a[1]
    assert a == M([1, 3])

    a = M([1, 2, 3])
    assert a[1:2] == M([2])
    a[1:2] = [4]
    assert a == M([1, 4, 3])
    del a[1:2]
    assert a == M([1, 3])

    assert 'abc'[M(1)] == 'b'

    a = M(2); b = 3; a -= b; assert a == M(2 - 3)
    a = M(2); b = 3; b -= a; assert b == M(3 - 2)

def test_dunder_multi():

    a = M(2, 1)

    assert a - 3 == M(2 - 3, 1 - 3)
    assert 3 - a == M(3 - 2, 3 - 1)

    assert divmod(a, 3) == M(divmod(2, 3), divmod(1, 3))
    assert divmod(3, a) == M(divmod(3, 2), divmod(3, 1))

    assert a & 6 == M(2 & 6, 1 & 6)
    assert 6 & a == M(6 & 2, 6 & 1)

    assert ~a == M(~2, ~1)
    assert -a == M(-2, -1)

    assert inner_complex(a) == M(complex(2), complex(1))

    assert not a <  1
    with raises(ValueError): bool(a <  2)
    assert     a <  3
    with raises(ValueError): bool(a <= 1)
    assert     a <= 2
    assert     a <= 3
    assert     a >= 1
    with raises(ValueError): bool(a >= 2)
    assert not a >= 3
    with raises(ValueError): bool(a >  1)
    assert not a >  2
    assert not a >  3

    assert not 1 >  a
    with raises(ValueError): bool(2 >  a)
    assert     3 >  a
    with raises(ValueError): bool(1 >= a)
    assert     2 >= a
    assert     3 >= a
    assert     1 <= a
    with raises(ValueError): bool(2 <= a)
    assert not 3 <= a
    with raises(ValueError): bool(1 <  a)
    assert not 2 <  a
    assert not 3 <  a

    if False:
        assert not a == 1
        assert     a == 2
        assert not a == 3
        assert     a != 1
        assert not a != 2
        assert     a != 3
        assert not 1 == a
        assert     2 == a
        assert not 3 == a
        assert     1 != a
        assert not 2 != a
        assert     3 != a

    a = M(True, False)
    with raises(ValueError): bool(a)
    a = M(True, True)
    assert a
    assert (a and False) == False
    assert (a or  False) == a
    a = M(False, False)
    assert not a
    assert (a and False) == a
    assert (a or  False) == False

    a = M('abc', 'ae')
    assert 'a' in a
    assert 'z' not in a
    with raises(ValueError): 'c' not in a
    assert a[1] == M('b', 'e')

    a = M([1, 2, 3], [4, 5])
    assert a[1] == M(2, 5)
    a[1] = 4
    assert a == M([1, 4, 3], [4, 4])
    del a[1]
    assert a == M([1, 3], [4])

    a = M([1, 2, 3], [4, 5, 6])
    assert a[1:2] == M([2], [5])
    a[1:2] = [4]
    assert a == M([1, 4, 3], [4, 4, 6])
    del a[1:2]
    assert a == M([1, 3], [4, 6])

    assert 'abc'[M(1, 1)] == 'b'
    with raises(ValueError):
        'abc'[M(1, 2)] == 'b'

    a = M(2, 4); b = 3; a -= b; assert a == M(2 - 3, 4 - 3)
    a = M(2, 4); b = 3; b -= a; assert b == M(3 - 2, 3 - 4)
