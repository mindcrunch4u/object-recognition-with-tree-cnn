import os
import base64
import io
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # FATAL
print("Loading tensorflow modules. Please standby...")
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import datasets, layers, models
from tensorflow.keras.models import Sequential
from copy import deepcopy
import numpy as np

import pathlib
from PIL import Image
#from skimage import transform
import pickle
import jieba
import difflib
import cv2
import paddle
'''
[
    { full_name : "universe" , child : [ ["universe","main"],["universe","expired"] ], predict_with : Obj_Loaded_Model },
    { full_name : ["universe", "main"], child : [ ... ] }
    # when there's nothing to "predict_with", then it's a stub
]
'''
def load_pickle( save_path ):
    save_path = str(save_path)
    save_path = pathlib.Path(save_path)
    try:
        obj = pickle.load( open( save_path, "rb" ) )
    except Exception as e:
        print(e)
        return None
    return obj

def image_preprop( image_data ):
    _IMAGE_HEIGHT=32
    _IMAGE_WIDTH=32
    _SCALE=255
    image_data = np.array(image_data).astype('float32')/_SCALE

    ## transform.resize is very slow
    #image_data = transform.resize(image_data, (_IMAGE_HEIGHT, _IMAGE_WIDTH, 3))
    image_data = cv2.resize(image_data, dsize=(_IMAGE_HEIGHT, _IMAGE_WIDTH), interpolation=cv2.INTER_CUBIC)
    return image_data

def load_image_b64_string( b64_string ):
    #NOTE remove data:image/... before sending in
    try:
        decoded_string = base64.b64decode(b64_string)
        buf = io.BytesIO(decoded_string)
        np_image = Image.open(buf)
        np_image = image_preprop( np_image )
        np_image = np.expand_dims(np_image, axis=0)
        return np_image
    except:
        return None

def load_image( image_path ):
    try:
        np_image = Image.open(image_path)
        np_image = image_preprop( np_image )
        np_image = np.expand_dims(np_image, axis=0)
        return np_image
    except:
        return None

def construct_fullname_list(model_file_name, root_dir_string):
    # topmost-level must be "universe"
    root_dir_list = root_dir_string.split(os.sep)
    _index = 0
    for item in root_dir_list:
        if item != 'dir-universe':
            _index += 1
        else:
            break
    _count = 0
    while _count < _index:
        _count += 1
        root_dir_list.pop(0)

    root_dir_list.append( model_file_name )
    _index = 0
    while _index < len(root_dir_list):
        name = root_dir_list[_index]
        name = name.replace("dir-","",1)
        name = name.replace("mod-","",1).split(".h5")[0]
        root_dir_list[_index] = name
        _index += 1

    return root_dir_list


class predictor:
    paddle.enable_static()
    jieba.enable_paddle()
    jieba.suggest_freq(('中', '将','然而'), True) # do seperate
    user_dict_location = ''

    @staticmethod
    def cut(joined_string):
        ret_list = jieba.cut_for_search( joined_string )
        return ret_list

    @staticmethod
    def configure(new_user_dict_location):
        # because all jieba instances share the same loaded dictionary
        # the configure method will be static, and reload user_dict once configured
        '''
            call routine:
            predictor.configure( 'user_dict.txt' )
            obj_predictor = predictor( None, None )
        '''
        predictor.user_dict_location = new_user_dict_location
        if os.path.isfile(predictor.user_dict_location):
            jieba.load_userdict(predictor.user_dict_location)
            print("inf: loaded user dict")
        else:
            print("err: user dict doesn\'t exist.")

    def get_node_by_fullname(self, fullname_list ):
        for item in self.list_of_table:
            if item["full_name"] == fullname_list:
                return item
        return None # <-- a stub will return non

    def __init__(self, path_to_cnn_tree_folder=None, path_to_match_dict=None):
        predictor.configure("./engine/dict.txt")
        self.list_of_table = list()
        self.list_of_match_dict = list()

        if path_to_match_dict != None:
            if self.load_match_dict(path_to_match_dict):
                print("inf: loaded text match dict")
            else:
                print("err: failed to load match dict")

        if path_to_cnn_tree_folder != None:
            if self.load_cnn_tree( path_to_cnn_tree_folder ):
                print("inf: loaded cnn predict tree")
            else:
                print("err: failed to load cnn predict tree")

    def predict(self, node_full_name, once_image_data ): # string : model_saved_as, :image: once_image_data
        node = self.get_node_by_fullname(node_full_name)
        if node == None:
            return None # <-- stub reached

        model = node["predict_with"]
        # image = load_image(image_path) #<-- slow, counter measure: load once, used many times
        predictions = model.predict( once_image_data )
        classes = np.argmax(predictions, axis = 1)
        picked_name = node["child"][classes[0]]
        picked_name = picked_name.replace("dir-","",1)

        ret_dict = dict()
        ret_name_list = node["full_name"] + [picked_name]

        ret_dict["full_name"] = ret_name_list 
        ret_dict["rate"] = predictions.flat[classes[0]]

        return ret_dict

    def recursive_predict(self, image_path):
        # default first node_full_name is "universe"
        once_image = load_image(image_path)
        name = self.predict(["universe"], once_image)
        last_record = None
        while name != None:
            last_record = name
            name = self.predict(name["full_name"], once_image)
        return last_record

    def recursive_predict_b64(self, b64_string):
        # default first node_full_name is "universe"
        once_image = load_image_b64_string(b64_string)
        name = self.predict(["universe"], once_image)
        last_record = None
        while name != None:
            last_record = name
            name = self.predict(name["full_name"], once_image)
        return last_record

    def load_match_dict(self, path_to_match_dict):
        t_match_dict = load_pickle(path_to_match_dict)
        if t_match_dict != None:
            self.list_of_match_dict = t_match_dict
            print("loaded match dict",path_to_match_dict," as: ", self.list_of_match_dict)
            return True
        else:
            print("err: fail to load match dict at: ", path_to_match_dict, "it\'s None")
            return False
    def load_cnn_tree(self, path_to_cnn_tree_folder):
        # loads the trained tree-cnn into memory
        if not os.path.isdir(path_to_cnn_tree_folder):
            print("err: cnn tree: cannot init with non-directory.")
            return False

        for root, dirs, files in os.walk(path_to_cnn_tree_folder, topdown=True):
            t_dict = dict()
            for one_file in files:
                # loading model into corresponding class(path)
                if one_file.startswith("mod-") and one_file.endswith(".h5"):
                    construct_node = dict()
                    t_model_path = os.path.join(root, one_file)
                    full_name = construct_fullname_list( one_file, root )
                    print("loading "+t_model_path+" into full name: "+str(full_name))

                    model_to_dir_name = full_name[-1]
                    paths_to_children = []
                    for lsdir in os.listdir( os.path.join(root,"dir-"+model_to_dir_name) ):
                        if os.path.isdir( os.path.join(root, "dir-"+model_to_dir_name, lsdir) ):
                            paths_to_children.append( lsdir )

                    paths_to_children = sorted(paths_to_children)
                    print("child: "+str(paths_to_children))
                    print("-----------------------------------")

                    construct_node["full_name"] = full_name
                    construct_node["child"] = paths_to_children # <-- sub-classes are trained in alphabetical order
                    construct_node["predict_with"] = tf.keras.models.load_model(t_model_path)

                    self.list_of_table.append( construct_node )
        return True

    #-------------------x predict text x---------------------
    '''
        call routine (predict):
            text_predictor = predictor( option1, option2 )
            text_predictor.match("string from OCR")
    '''
    def match(self, str_query):
        if self.list_of_match_dict == None or self.list_of_match_dict == []:
            print("err: match_dict wasn\'t loaded at all.")
            return None # match_dict wasn't loaded

        # expecting "str_query" to be joined, space removed before passing in
        search_list = jieba.cut_for_search( str_query )
        search_list = list(filter(lambda a: a != ' ', search_list)) # remove all spaces
        search_list = ''.join(search_list)
        search_list = list(jieba.cut_for_search( str_query ))
        search_list = list(filter(lambda a: a != ' ', search_list)) # remove all spaces

        print("predictor searching for list: ",search_list) 
        top_score = -1
        top_class_name = None
        top_class_parent = None
        for item in self.list_of_match_dict:
            try:
                for line in item["list_match_text"]:
                    #match_score = difflib.SequenceMatcher(None, str_query, line).ratio()
                    match_score = difflib.SequenceMatcher(None, search_list, line).ratio()
                    if match_score > top_score:
                        top_score = match_score
                        top_class_name = item["name"]
                        top_class_parent = item["parent_list"]
            except:
                continue
        ret_dict = dict()
        ret_dict["full_name"] = []
        ret_dict["full_name"] += top_class_parent
        ret_dict["full_name"].append(top_class_name)
        ret_dict["rate"] = top_score
        print("TODO from predictor returns: ",ret_dict)

        return ret_dict


if __name__ == '__main__':
    a = predictor(path_to_cnn_tree_folder="./all_models", path_to_match_dict="./match_dict.dat")

    st = "品牌: 铁工厂 型号: 899 材质: 皮革 图案: 艺术 风格: 北欧 颜色分类: 魅力橙色【头层牛皮】单椅 魅力橙色【头层牛皮】单椅+脚踏 魅力橙色【科技皮】单椅 魅力橙色【科技皮】单椅+脚踏 毛重: 30 填充物: 高弹泡沫海绵 是否可定制: 是 适用对象: 成人 是否可拆换: 沙发套不可拆换 产地: 广东省 "
    ret = a.match(st)
    print(ret)

    ret = a.recursive_predict("./Image_10.jpg")
    print(ret)

    path="./Image_10.jpg"
    encoded_string = ''
    with open(path,"rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    ret = a.recursive_predict_b64(encoded_string)
    print(ret)
