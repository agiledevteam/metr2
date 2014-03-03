
import redis
import pickle


def main():
  r = redis.Redis()
  for key in r.keys("codefat:*"):
    row = [key] + list(pickle.loads(r.get(key)))
    for cell in row:
      print cell,
    print


if __name__ == '__main__':
  main()

