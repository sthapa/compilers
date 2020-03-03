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
  """
  Print out the names of functions defined in given ast.AST object
  """
  def generic_visit(self, node: ast.AST):
    if node.__class__ == ast.FunctionDef:
      sys.stdout.write(f"Defining function: {node.name} \n")
    super().generic_visit(node)


class FunctionVisitor(ast.NodeVisitor):
  """
  Print out the names of functions defined in given ast.AST object
  """
  def visit_FunctionDef(self, node: ast.FunctionDef):
    sys.stdout.write(f"Defining function: {node.name} \n")


class UnusedVariables(ast.NodeVisitor):
  """
  Print out variables that are set but might be unused
  """

  def __init__(self):
    super().__init__()
    self.variable_def = {'global': {}}
    self.variable_used = {'global': {}}
    self.stack = ["global"]
    self.function_name = "global"

  def visit_FunctionDef(self, node: ast.FunctionDef):
    self.function_name = node.name
    self.stack.append(node.name)
    self.variable_def[node.name] = {}
    super().generic_visit(node)
    for var in self.variable_def[node.name]:
      if var not in self.variable_used[node.name]:
        line = self.variable_def[node.name][var]['line']
        sys.stdout.write(f"Variable {var} defined in {node.name} on line {line} not used")
    del self.variable_used[node.name]
    del self.variable_def[node.name]
    # remove function information
    self.function_name = self.stack.pop()
    self.function_name = self.stack[-1]

  def visit_Nonlocal(self, node: ast.Nonlocal):
    if 'nonlocal' in self.variable_def[self.function_name]:
      nonlocal_vars = self.variable_def[self.function_name]['nonlocal']
      if node.id not in nonlocal_vars:
        self.variable_def[self.function_name]['nonlocal'].append(node.id)
    else:
      self.variable_def[self.function_name]['nonlocal'] = [node.id]

  def visit_Global(self, node: ast.Global):
    if 'global' in self.variable_def[self.function_name]:
      nonlocal_vars = self.variable_def[self.function_name]['global']
      if node.id not in nonlocal_vars:
        self.variable_def[self.function_name]['global'].append(node.id)
    else:
      self.variable_def[self.function_name]['global'] = [node.id]

if __name__ == '__main__':
  main()
