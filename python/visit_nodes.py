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

  sys.stdout.write("----\nChecking for unused variables\n-----\n")
  check_usage = UnusedVariables()
  check_usage.check(tree)


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
    self.variable_def = {'global': {'global': [],
                                    'nonlocal': [],
                                    'local': []}}
    self.variable_used = {'global': {}}
    self.stack = ["global"]
    self.function_name = "global"

  def check(self, node: ast.AST) -> None:
    self.generic_visit(node)
    for var in self.variable_def['global']['local']:
      if var[0] not in self.variable_used['global']:
        sys.stdout.write(f"Variable {var[0]} defined in global on line {var[2]} not used\n")

  def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
    self.function_name = node.name
    self.stack.append(node.name)
    self.variable_used[node.name] = {}
    self.variable_def[node.name] = {'global': [],
                                    'nonlocal': [],
                                    'local': []}
    for arg in node.args.args:
      self.variable_def[node.name]['local'].append((arg.arg, node.name, node.lineno))
    super().generic_visit(node)
    for var in self.variable_def[node.name]['local']:
      if var[0] not in self.variable_used[node.name]:
        sys.stdout.write(f"Variable {var[0]} defined in {node.name} on line {var[2]} not used\n")
    del self.variable_used[node.name]
    del self.variable_def[node.name]
    # remove function information
    self.function_name = self.stack.pop()
    self.function_name = self.stack[-1]

  def register_variable(self, scope: str, var_name: str, line: int) -> None:
    if scope in self.variable_def[self.function_name]:
      if var_name not in [x[0] for x in self.variable_def[self.function_name][scope]]:
        self.variable_def[self.function_name][scope].append((var_name, self.function_name, line))
    else:
      self.variable_def[self.function_name][scope] = [(var_name, self.function_name, line)]

  def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
    for name in node.names:
      self.register_variable('nonlocal', name, node.lineno)

  def visit_Global(self, node: ast.Global) -> None:
    for name in node.names:
      self.register_variable('global', name, node.lineno)

  def visit_Assign(self, node: ast.Assign) -> None:
    # register the LHS of assignment
    if isinstance(node.targets[0], ast.Name):
      self.register_variable('local', node.targets[0].id, node.lineno)

    # examine the RHS of assignment
    super().generic_visit(node.value)

  def visit_Call(self, node: ast.Call) -> None:
    # visit parameters and register them
    for arg in node.args:
      if isinstance(arg, ast.Name):
        self.register_usage(arg.id)

  def var_defined(self, scope: str, var_name: str, function: str = None) -> bool:
    if function is None:
      function = self.function_name
    return var_name in [x[0] for x in self.variable_def[function][scope]]

  def register_usage(self, var_name: str) -> None:

    # if we know the var is global we can short-circuit the registration
    if self.var_defined('global', var_name):
      if var_name not in self.variable_used['global']:
        self.variable_used['global'][var_name] = True
        return

    # otherwise we need to check up the stack
    for function in reversed(self.stack):
      # short circuit global vars
      if self.var_defined('global', var_name, function):
        if var_name not in self.variable_used['global']:
          self.variable_used['global'][var_name] = True
          return

      # nonlocal variables are defined deeper in the stack
      if self.var_defined('nonlocal', var_name, function):
        continue

      # if definition found, mark var as being used and exit
      if self.var_defined('local', var_name, function):
        if var_name not in self.variable_used[function]:
          self.variable_used[function][var_name] = True
          return

      # continue going deeper in the stack to find the variable

    # if we're here, we haven't found the variable anywhere
    sys.stdout.write(f"In {self.function_name}, {var_name} used without being defined\n")

  def visit_Name(self, node: ast.Name) -> None:
    self.register_usage(node.id)


if __name__ == '__main__':
  main()
