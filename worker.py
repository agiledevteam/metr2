import redis
from pickle import loads, dumps

r = redis.Redis()

def queue_daemon(app, rv_ttl=500):
  while 1:
    msg = r.blpop('metrapp:queue')
    func, key, args, kwargs = loads(msg[1])
    try:
      rv = func(*args, **kwargs)
    except Exception, e:
      rv = e
    if rv is not None:
      r.set(key, dumps(rv))
      r.expire(key, rv_ttl)
