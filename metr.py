import os
import sys
from collections import namedtuple
import re

test_pattern = re.compile('tests?$', re.IGNORECASE)

import plyj.parser as plyj
import plyj.model as java

parser = plyj.Parser()

def metr(input):
  tree = parser.parse_string(input)
  exes = find_executables(tree)
  return stat_sum(exe.stat() for exe in exes)

def stat_sum(stats):
  cc = 0
  sloc = 0
  dloc = 0
  for stat in stats:
    cc += stat.cc -1
    sloc += stat.sloc
    dloc += stat.dloc
  return Stat(cc+1, sloc, dloc) 

def find_executables(tree):
  visitor = TreeVisitor(False)
  tree.accept(visitor)
  return visitor.executables()

class TreeVisitor(java.Visitor):
  def __init__(self, verbose=False):
    super(TreeVisitor,self).__init__(verbose)
    self.exes = []

  def visit_MethodDeclaration(self, decl):
    if decl.body != None:
      self.exes.append(Executable(toStmt(decl.body)))
    return True

  def visit_ConstructorDeclaration(self, decl):
    self.exes.append(Executable(toStmt(decl.block)))
    return True
  
  def executables(self):
    return self.exes

def toStmt(stmt):
  if isinstance(stmt, list):
    return BlockStmt([toStmt(each) for each in stmt])
  elif isinstance(stmt, java.Block):
    return BlockStmt([toStmt(each) for each in stmt.statements])
  elif isinstance(stmt, java.IfThenElse):
    return IfStmt(toStmt(stmt.if_true), toStmt(stmt.if_false) if stmt.if_false != None else None)
  elif isinstance(stmt, java.DoWhile):
    return LoopStmt('do', toStmt(stmt.body))
  elif isinstance(stmt, java.While):
    return LoopStmt('while', toStmt(stmt.body))
  elif isinstance(stmt, (java.For, java.ForEach)):
    return LoopStmt('for', toStmt(stmt.body))
  elif isinstance(stmt, java.Try):
    return TryStmt(toStmt(stmt.block), 
      [toStmt(each.block) for each in stmt.catches], 
      toStmt(stmt._finally) if stmt._finally != None else None)
  elif isinstance(stmt, java.Switch):
    cases = []
    for caseGroup in stmt.switch_cases:
      cases += [toStmt([]) for x in caseGroup.cases[:-1]]
      cases += [toStmt(caseGroup.body)]
    return SwitchStmt(cases)
  elif isinstance(stmt, java.Synchronized):
    return SyncStmt(toStmt(stmt.body))
  elif isinstance(stmt, java.Empty):
    return BlockStmt([])
  elif stmt == None:
    return BlockStmt([])
  else:
    return Stmt()

Stat = namedtuple('Stat', ['cc', 'sloc', 'dloc'])

class Executable(object):
  def __init__(self, body):
    self.body = body
  def stat(self):
#    self.body.dump()
    return Stat(self.cc(), self.sloc(), self.dloc())
  def cc(self):
    return self.body.cc() + 1
  def sloc(self):
    return self.body.loc(1)
  def dloc(self):
    return self.body.loc(0.5)

class Stmt(object):
  def __init__(self, name = 'other'):
    self.name = name 

  def cc(self):
    return 0

  def loc(self,df):
    return 1

  def dump(self, depth=0):
    print ' '*depth, self.name, self.loc(1)
    for child in self.children():
      child.dump(depth+1)

  def children(self):
    return []
  
class IfStmt(Stmt):
  # elsePart can be None
  def __init__(self, thenPart, elsePart):
    super(IfStmt, self).__init__('if')
    self.thenPart = thenPart
    self.elsePart = elsePart

  def cc(self):
    return 1 + self.thenPart.cc() + self.elsePart.cc() if self.elsePart != None else 0

  def loc(self,df):
    return sum(each.loc(df) * df + 1 for each in self.ifElseChain())

  def ifElseChain(self):
    cur = self
    parts = []
    while cur != None and cur.name == 'if':
      parts.append(cur.thenPart)
      cur = cur.elsePart
    if cur != None:
      parts.append(cur)
    return parts

  def children(self):
    if self.elsePart != None:
      return [self.thenPart, self.elsePart]
    else:
      return [self.thenPart]

class SwitchStmt(Stmt):
  def __init__(self, cases):
    super(SwitchStmt, self).__init__('switch')
    self.cases = cases

  def cc(self):
    return sum(each.cc() + 1 for each in self.cases)

  def loc(self, df):
    return 1 + sum(each.loc(df) * df + 1 for each in self.cases)

  def children(self):
    return self.cases

class LoopStmt(Stmt):
  def __init__(self, name, body):
    super(LoopStmt, self).__init__(name)
    self.body = body

  def cc(self):
    return self.body.cc() + 1

  def loc(self, df):
    if self.name == 'do':
      return 2 + self.body.loc(df) * df
    else:
      return 1 + self.body.loc(df) * df

  def children(self):
    return [self.body]

class BlockStmt(Stmt):
  def __init__(self, statements):
    super(BlockStmt, self).__init__('block')
    self.statements = statements

  def cc(self):
    return sum(each.cc() for each in self.statements)

  def loc(self, df):
    return sum(each.loc(df) for each in self.statements)

  def children(self):
    return self.statements
    
class SyncStmt(Stmt):
  def __init__(self, body):
    super(SyncStmt, self).__init__('sync')
    self.body = body

  def cc(self):
    return self.body.cc()

  def loc(self, df):
    return 1 + self.body.loc(df)

class TryStmt(Stmt):
  # finalizer can be None
  def __init__(self, body, catchers, finalizer):
    super(TryStmt, self).__init__('try')
    self.body = body
    self.catchers = catchers
    self.finalizer = [finalizer] if finalizer != None else []

  def cc(self):
    return sum(each.cc() for each in [self.body] + self.catchers + self.finalizer)

  def loc(self, df):
    return sum(each.loc(df) + 1 for each in [self.body] + self.catchers + self.finalizer)

  def children(self):
    return [self.body] + self.catchers + self.finalizer

def find_files(dir):
  for dirname, dirnames, filenames in os.walk(dir):
    for filename in filenames:
      if filename[-5:] != '.java':
        continue
      yield os.path.join(dirname, filename)
    for dir in dirnames:
      if test_pattern.search(dir) != None:
        dirnames.remove(dir)

def metr_file(arg):
  f = open(arg,'rU')
  print arg, metr(f.read())
  f.close()
  
def run_metr(arg):
  if os.path.isdir(arg):
    for file in find_files(arg):
      metr_file(file) 
  elif os.path.isfile(arg):
    try:
      metr_file(arg)
    except Exception as e:
      raise
  else:
      print "Can't open file/directory : %s" % (arg)

def main(argv):
  if len(argv) == 0:
    print 'No arguments. Specify <dir> or <file>'
    return
  else:
    for a in argv:
      run_metr(a)
    

if __name__ == '__main__':
  main(sys.argv[1:])

