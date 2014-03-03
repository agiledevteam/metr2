import redis
r = redis.Redis()
r.flushdb()


from metrapp import app

client = app.test_client() 
client.get("/api/trend")
