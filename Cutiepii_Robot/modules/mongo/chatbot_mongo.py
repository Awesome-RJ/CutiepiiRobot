from Cutiepii_Robot import mongodb as db_x

cutiepii = db_x["CHATBOT"]


def add_chat(chat_id):
    stark = cutiepii.find_one({"chat_id": chat_id})
    if stark:
        return False
    else:
        cutiepii.insert_one({"chat_id": chat_id})
        return True


def remove_chat(chat_id):
    stark = cutiepii.find_one({"chat_id": chat_id})
    if not stark:
        return False
    else:
        cutiepii.delete_one({"chat_id": chat_id})
        return True


def get_all_chats():
    r = list(cutiepii.find())
    if r:
        return r
    else:
        return False


def get_session(chat_id):
    stark = cutiepii.find_one({"chat_id": chat_id})
    if not stark:
        return False
    else:
        return stark
