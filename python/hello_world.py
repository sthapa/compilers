#!python3

import argparse
import ast
import sys


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-f", "--filename", action="store", type=str, help="file to parse", default="example.py")
  args = parser.parse_args()
  with open(args.filename, "r") as source:
    tree = ast.parse(source.read())
  sys.stdout.write("Visiting nodes using generic_visit:\n")
  hello_visitor = HelloVisitor()
  hello_visitor.visit(tree)
  sys.stdout.write("Visiting nodes using specific visit function:\n")
  function_visitor = FunctionVisitor()
  function_visitor.visit(tree)


class HelloVisitor(ast.NodeVisitor):

  def generic_visit(self, node):
    if node.__class__ == ast.FunctionDef:
      sys.stdout.write(f"Defining function: {node.name} \n")
    super().generic_visit(node)


class FunctionVisitor(ast.NodeVisitor):

  def visit_FunctionDef(self, node):
    sys.stdout.write(f"Defining function: {node.name} \n")


if __name__ == '__main__':
  main()
