#!python3


def test_function():
  """Docstring test"""
  # no messages
  a = 5
  return a


def test_function2(a, b, c):
  """Docstring test 2"""
  # should get message about a and c being unused
  b = 10
  a = 20 + b

def test_nested():
  # no messages
  foo = 10

  def bar():
    nonlocal foo
    print(foo)

  print("abc")

def test_traversal():
  # no messages

  bar = 20

  def foo():
    print(bar)

  print(baz)


if __name__ == '__main__':
  # should get message about unused
  baz = "hello"
  unused = "world"

  test_function()
  test_function2(20, 30, 40)
  test_nested()
  test_traversal()
