from redis import Redis
import pickle

redis = Redis()
def rediscache(key_prefix, seconds=24*60*60):
  def wrap(func):
    def wrapped(*args):
      key = ":".join([key_prefix] + list(args))
      result = redis.get(key)
      if result == None:
        result = func(*args)
        redis.set(key, pickle.dumps(result))
        redis.expire(key, seconds)
      else:
        result = pickle.loads(result)
      return result
    return wrapped
  return wrap