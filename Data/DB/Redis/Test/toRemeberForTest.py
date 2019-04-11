
if __name__ == "__name__":
    redis_client = Redis()
    value = redis_client.get('plop')
    print(value)
