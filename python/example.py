#!python3


def test_function():
  """Docstring test"""
  print(5)
  if False:
    print(10)


def test_function2(a, b, c):
  """Docstring test 2"""
  print(a)
  print(b)
  if False:
    print(10)


if __name__ == '__main__':
  if None:
    print(1)
  else:
    print(2)

  if True:
    print(3)
  else:
    print(4)

  if False:
    print(5)
  else:
    print(6)


  test_function()
  test_function2(20, 30, 40)