import metr
import unittest

class MetrTest(unittest.TestCase):
  
  def testEmpty(self):
    self.assertEqual(metr.Stat(0, 0), metr.metr('class X {}'))
  
  def testSingleMethod(self):
  	stat = metr.metr('''class X {
	  		void x() {
	  			return;
	  		}
  		}''')
  	self.assertEqual(metr.Stat(1,0), stat)

  def testInitializer(self):
  	stat = metr.metr('''class X {
  			int a;
  			{
  				a = 0;
  				for (int i = 0; i<10; i++) {
  					a += i;
  				}
  			}
  		}''')
  	self.assertEqual(metr.Stat(3,0.5), stat)

  def testStaticInitializer(self):
  	stat = metr.metr('''class X {
  			static int a;
  			static {
  				a = 0;
  				for (int i = 0; i<10; i++) {
  					a += i;
  				}
  			}
  		}''')
  	self.assertEqual(metr.Stat(3,0.5), stat)

  def testAnonymousClass(self):
  	stat = metr.metr('''class X {
  			X() {
  				Y.addListener(new Runnable() {
  					void run() {
  						return;
  					}
  				});
  			}
  		}''')
  	self.assertEqual(metr.Stat(2, 0), stat)

  def testTypeHierarchy(self):
  	expected = [
  		metr.Entry('X', 'X', metr.Stat(1,0)),
  		metr.Entry('X.$Runnable', 'run', metr.Stat(1,0)),
  		metr.Entry('X.Y', 'y', metr.Stat(1,0))
  	]
  	entries = metr.entries('''
  		class X {
  			X() {
  				Y.addListener(new Runnable() {
  					void run() {
  						return;
  					}
  				});
  			}
  			class Y {
  				Z y() {
  					return new Z();
  				}
  			}
  		}
  		''')

  	self.assertEqual(expected, list(entries))


  def testDeepTypeHierarchy(self):
  	expected = [
  		metr.Entry('X.Y', 'y', metr.Stat(1,0)),
  		metr.Entry('X.Y.$O.P.Q.Z', 'foo', metr.Stat(1,0))
  	]
  	entries = metr.entries('''
  		class X {
  			class Y {
  				Z y() {
  					return O.P.new Q<R>.Z() {
  						void foo() {
  							return;
  						}
  					};
  				}
  			}
  		}
  		''')

  	self.assertEqual(expected, list(entries))

  def testEnum(self):
  	expected = [
  		metr.Entry('Z.A', 'zar', metr.Stat(1,0)),
  		metr.Entry('Z.B', 'zar', metr.Stat(1,0)),
  		metr.Entry('Z', 'Z', metr.Stat(1,0)),
  		metr.Entry('Z', 'bar', metr.Stat(1,0))
  	]
  	entries = metr.entries('''
  		
  			enum Z {
  			  A(1) {
  			    void zar() {
  			    	log();
  			    }
  			  }, B(2) {
  			    void zar() {
  			        log();
  			    }
  			  };
  			  Z(int x) {
  			    log(x);
  			  }
  			  void bar() {
  			  	log();
  			  }
  			  abstract void zar();
  			}

  			enum C {
  			  D, E
  			}
  		
  		''')

  	self.assertEqual(expected, list(entries))

  def testThrowException(self):
  	expected = [metr.Entry('X', 'foo', metr.Stat(1,0)),
  		metr.Entry('X.$Exception', 'toString', metr.Stat(1,0))]
  	entries = metr.entries('''
  		class X {
  		  void foo() throws Exception {
  		    throw new Exception() {
  		    	@Override
  		    	public String toString() {
  		    		return "";
  		    	}
  		    };
  		  }
  		}
  		''')
  	self.assertEquals(expected, list(entries))


  def testWhileNesting(self):
  	expected = [metr.Entry('X', 'x', metr.Stat(3,0.5)),
  		metr.Entry('X.$Runnable', 'run', metr.Stat(0,0))]
  	entries = metr.entries('''class X {
	  		void x() {
	  			int x = 10;
	  			while(x-- > 0)
	  				new Thread(new Runnable() {
	  					@Override public void run() {

	  					}
	  				}).start();
	  		}
  		}''')
  	self.assertEquals(expected, list(entries))
