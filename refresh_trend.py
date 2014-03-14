import redis
r = redis.Redis()
r.delete(*r.keys("codefat:*"))

from metrapp import app

client = app.test_client() 
client.get("/api/trend")
