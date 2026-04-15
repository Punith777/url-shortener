BASE62 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def encode(num):
    if num == 0:
        return BASE62[0]

    result = []
    while num > 0:
        rem = num % 62
        result.append(BASE62[rem])
        num //= 62

    return "".join(result[::-1])