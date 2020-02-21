#!python3

import argparse
import ast
import collections
import copy
import sys
import timeit

import astpretty


def time_tree(tree: ast.AST):
  """
  Time ast execution

  :param tree: AST tree
  :return: float recording number of seconds to run snippet
  """
  return timeit.timeit(stmt="exec(compile(tree, 'test', mode='exec'))", number=10000, globals={'tree': tree})


class RemoveDeadCode(ast.NodeTransformer):
  """
  Simplify branches that test constants to remove dead code
  e.g. if true: a = 5 else a = 10  gets turned into a = 5
  """

  def visit_If(self, node):
    # make sure to recurse on branches
    super().generic_visit(node)

    if type(node.test) in [ast.Constant, ast.NameConstant]:
      if node.test.value:
        new_node = node.body
      else:
        new_node = node.orelse

      if not new_node:
        # if branch being used is empty, delete
        return None
      return new_node
    else:
      return node

  def optimize(self, node: ast.AST):
    """
    Optimize nodes

    :param node: node to optimize
    :return: ast tree
    """
    new_node = self.visit(node)
    ast.fix_missing_locations(new_node)
    return new_node


class CallOnlyChecker(ast.NodeVisitor):
  """
  Visit and check function definitions to make sure that it can be inlined,
  i.e. make sure function only consists of calls

  Also cache function defs so that they can later be inlined
  """

  def __init__(self):
    self.__function_cache__ = collections.defaultdict(lambda: {'args': [], 'body': []})
    self.__inlineable_cache__ = collections.defaultdict(lambda: False)
    super().__init__()

  def can_inline(self, name: str) -> bool:
    """
    Check to see if function can be inlined

    :param name: name of function to check
    :return: True if function can be inlined, False otherwise
    """
    return self.__inlineable_cache__[name]

  def get_cached_function(self, name: str) -> dict:
    """
    Get dictionary with function information

    :param name: name of function
    :return: a
    """
    return copy.copy(self.__function_cache__[name])

  def visit_FunctionDef(self, node: ast.FunctionDef):
    """
    Examine function and cache if needed
    :param node: ast.FunctionDef to analyze
    :return: None
    """
    for func_node in ast.iter_child_nodes(node):
      if isinstance(func_node, ast.Expr) and type(func_node.value) in [ast.Str, ast.Call]:
        next
      elif isinstance(func_node, ast.arguments):
        next
      else:
        self.__inlineable_cache__[node.name] = False
        return
    self.__inlineable_cache__[node.name] = True
    self.__function_cache__[node.name] = {'args': node.args}
    if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
      # skip docstring
       call_list = node.body[1:]
    else:
      call_list = node.body
    call_list = map(lambda x: x.value, call_list)
    self.__function_cache__[node.name]['body'] = call_list


class InlineFunctions(ast.NodeTransformer):
  """Inline functions that only have calls in them"""

  def __init__(self):
    self.checker = CallOnlyChecker()
    super().__init__()

  def optimize(self, tree: ast.AST):
    """
    verify and inline functions if functions only consist of calls
    :param tree: ast node
    :return: None
    """

    # get information about ast
    self.checker.visit(tree)
    inlined_tree = self.visit(tree)
    inlined_tree = CleanupAST().cleanup(inlined_tree)
    ast.fix_missing_locations(inlined_tree)
    return inlined_tree

  def visit_Call(self, node):
    """
    Look at function calls and replace if possible
    """
    super().generic_visit(node)
    if self.checker.can_inline(node.func.id):
      replacement_code = self.checker.get_cached_function(node.func.id)
      replacement_args = replacement_code['args']
      replacement_nodes = []
      replacement_table = {}
      index = 0
      for arg in node.args:
        arg_name = replacement_args.args[index].arg
        replacement_table[arg_name] = arg
        index += 1
      for call in replacement_code['body']:
        new_args = []
        for arg in call.args:
          if isinstance(arg, ast.Name):
            if arg.id in replacement_table:
              new_args.append(replacement_table[arg.id])
            else:
              new_args.append(arg)
          else:
            new_args.append(arg)
        call.args = new_args
        replacement_nodes.append(call)
      if len(replacement_nodes) == 1:
        return replacement_nodes[0]
      else:
        for node in replacement_nodes:
          node.lineno = 0

      return replacement_nodes
    else:
      return node


class CleanupAST(ast.NodeTransformer):
  """
  Scan and cleanup ASTs to split Expr nodes with values that contain multiple
  expressions
  """

  def cleanBody(self, node_body: list) -> list:
    """
    Clean up expr nodes in a list, splitting expr with
    multiple statements in value field

    :param node_body: list of ast nodes
    :return: list of cleaned ast nodes
    """
    new_body = []
    for child_node in node_body:
      if isinstance(child_node, ast.Expr) and isinstance(child_node.value, list):
          if len(child_node.value) == 1:
            new_body.append(ast.Expr(value=child_node.value[0]))
          else:
            for stmt in child_node.value:
              new_body.append(ast.Expr(value=child_node.value[0]))
      else:
        new_body.append(child_node)
    return new_body

  def visit_Module(self, node: ast.Module):
    """
    Clean up expr nodes in a module

    :param node: ast.Module instance to cleanup
    :return: cleaned up node
    """
    super().generic_visit(node)

    node.body = self.cleanBody(node.body)
    return node

  def visit_FunctionDef(self, node: ast.FunctionDef):
    """
    Examine function and clean up if necessary
    :param node: ast.FunctionDef to analyze
    :return: None
    """
    super().generic_visit(node)

    node.body = self.cleanBody(node.body)
    return node

  def visit_If(self, node: ast.FunctionDef):
    """
    Examine if statement and clean up if necessary
    :param node: ast.FunctionDef to analyze
    :return: None
    """
    super().generic_visit(node)


    node.body = self.cleanBody(node.body)
    node.orelse = self.cleanBody(node.orelse)
    return node

  def cleanup(self, tree: ast.AST) -> ast.AST:
    """
    Clean up an AST tree, splitting incorrect Expr if found

    :param tree: AST to clean
    :return: cleaned AST
    """
    new_tree = self.visit(tree)
    ast.fix_missing_locations(new_tree)
    return new_tree


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-f", "--filename", action="store", type=str, help="file to parse", default="example.py")
  args = parser.parse_args()
  with open(args.filename, "r") as source:
    tree = ast.parse(source.read())

  sys.stdout.write(f"AST  code:\n")
  astpretty.pprint(tree)
  code_timing = time_tree(tree)
  branch_transformer = RemoveDeadCode()
  pruned_tree = branch_transformer.optimize(tree)
  deadcode_timing = time_tree(pruned_tree)
  sys.stdout.write(f"transformed AST  code:\n")
  astpretty.pprint(pruned_tree)

  function_transformer = InlineFunctions()

  inlined_tree = function_transformer.optimize(pruned_tree)
  astpretty.pprint(inlined_tree)

  inlined_tree = ast.fix_missing_locations(inlined_tree)
  inlined_code_timing = time_tree(inlined_tree)
  sys.stdout.write(f"inlined AST  code:\n")
  astpretty.pprint(inlined_tree)
  sys.stdout.write(f"Time for code: {code_timing}\n")
  sys.stdout.write(f"Time for code after using RemoveDeadCode: {deadcode_timing}\n")
  sys.stdout.write(f"Time for code after using RemoveDeadCode and InlineFunction: {inlined_code_timing}\n")


if __name__ == '__main__':
  main()
