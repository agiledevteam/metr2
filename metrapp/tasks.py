from workqueue import queuefunc

@queuefunc
def add(a, b):
    return a + b