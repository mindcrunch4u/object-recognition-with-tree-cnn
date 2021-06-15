# manage all db read/write
from pymongo import MongoClient
from pprint import pprint
from bson.objectid import ObjectId

def inf( message ):
    print("[inf]", message)
def err( message ):
    print("[err]", message)

class db:
    client = None
    db = None
    admin = None
    mongo_url = "127.0.0.1:27017"
    fixed_db_string = "dasAuge"
    def is_setup(self):
        if self.client != None and self.admin != None and self.db != None:
            return True
        return False

    def __init__(self):
        self.client = MongoClient(self.mongo_url)
        self.admin = self.client.admin
        self.db = self.client[self.fixed_db_string]

    def status(self):
        return self.admin.command("serverStatus")

    def get_list_of_post_by_model_id(self, model_id ):
        if not self.is_setup:
            return None
        collection = self.db[str(model_id)]
        cursor = collection.find({})
        ret_list = []
        for document in cursor:
            tmp_dict = dict()
            tmp_dict["model_id"] = str(model_id)
            tmp_dict["post_id"] = str(document["post_id"])
            tmp_dict["post_name"] = str(document["post_name"])
            ret_list.append(tmp_dict)
        return ret_list

    def get_post_by_id(self, model_id, post_id ):
        model_id = str(model_id)
        post_id = str(post_id)
        document = self.db[model_id].find_one({"post_id":str(post_id)})
        if document:
            ret_dict = dict()
            ret_dict["name"] = document["post_name"]
            ret_dict["content"] = document["content"]
            return ret_dict
        else:
            return None

    def is_key_valid(self, key): #TODO
        return True

    def is_fullname_exist(self, model_id, fullname):
        #NOTE every time flask starts(init with tree), make sure each "fullname" has its description
        #NOTE fullname is a list
        return self.db[str(model_id)].find({"fullname":fullname}).limit(1).count() > 0

    def create_post_by_id(self, model_id, post_id, post_name, fullname, content):
        if not self.is_setup:
            return False
        if self.db[str(model_id)].find({"post_id":post_id}).limit(1).count() <= 0:
            data_dict = {
                    "post_id":post_id,
                    "post_name":post_name,
                    "fullname":fullname,
                    "content":content
                }
            collection = self.db[str(model_id)]
            collection.insert_one(data_dict)
            inf("created post: "+str(post_id))
        else: # if post found, update it
            self.update_post_by_id(model_id, post_id, content)
        return True

    def update_post_by_id(self, model_id, post_id, content):
        if not self.is_setup:
            return False
        if self.db[str(model_id)].find({"post_id":post_id}).limit(1).count() <= 0:
            return False # <-- post wasn't there yet
        collection = self.db[str(model_id)]
        update_filter = { 'post_id':post_id }
        data_to_update = { "$set": { 'content':content }}
        collection.update_one(update_filter, data_to_update)
        inf("updated post with id: " + str(post_id))
        return True

    def get_post_id_by_fullname(self, model_id, class_fullname ):
        document = self.db[str(model_id)].find_one({"fullname":class_fullname})
        if document:
            return document["post_id"]
        else:
            return None

    def get_list_of_model_id(self):
        ret_list = self.db.collection_names()
        try:
            ret_list.remove('system.indexes')
        except:
            pass
        return ret_list




if __name__ == '__main__':
    conn = db()
    conn.status()
    conn.create_post_by_id("furnitures","001","furnitures, chairs, model a", ["furnitures","chairs","model a"],"<p>no</p>")
    conn.update_post_by_id("furnitures","001","<p>yes nooo!!</p>")
    post_list = conn.get_list_of_post_by_model_id("furnitures")
    id_from_fullname = conn.get_post_id_by_fullname("furnitures", ["furnitures","chairs","model a"] )
    list_of_models = conn.get_list_of_model_id()
    #print(list_of_models)
    #print(id_from_fullname)
    #print(post_list)
