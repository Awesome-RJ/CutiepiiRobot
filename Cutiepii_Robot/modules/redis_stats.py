from Cutiepii_Robot import REDIS

# will put redis python commands here later 

# total keys in redis db
def __stats__():
    return f"• {len(REDIS.keys())} Total Keys in Redis Database."
    
__mod_name__ = "Redis"

# def __help__():
#    return f"testing something"
