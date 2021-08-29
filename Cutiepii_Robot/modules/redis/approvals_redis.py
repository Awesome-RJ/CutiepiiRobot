from Cutiepii_Robot import REDIS

try:
    eval(REDIS.get("Approvals"))
except BaseException:
    REDIS.set("Approvals", "{}")


def approve(chat_id, user_id):
    approved = eval(REDIS.get("Approvals"))
    try:
        list = approved[chat_id]
        if user_id not in list:
            list.append(user_id)
        approved.update({chat_id: list})
    except BaseException:
        approved.update({chat_id: [user_id]})
    return REDIS.set("Approvals", str(approved))


def disapprove(chat_id, user_id):
    approved = eval(REDIS.get("Approvals"))
    try:
        list = approved[chat_id]
        if user_id in list:
            list.remove(user_id)
        approved.update({chat_id: list})
    except BaseException:
        pass
    return REDIS.set("Approvals", str(approved))


def is_approved(chat_id, user_id):
    approved = eval(REDIS.get("Approvals"))
    try:
        list = approved[chat_id]
        if user_id in list:
            return True
        return
    except BaseException:
        return


def list_approved(chat_id):
    approved = eval(REDIS.get("Approvals"))
    try:
        list = approved[chat_id]
        return list
    except BaseException:
        return
