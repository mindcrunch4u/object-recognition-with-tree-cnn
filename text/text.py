import os
import jieba
import difflib
import sys
import pathlib
from copy import deepcopy
from components.utils import save_pickle, load_pickle
from components.node import node


class text():

    user_dict_location = None
    user_stopwords_location = None
    stopwords_list = []
    #add_dict = None
    gathered_info = None

    def __init__(self, user_dict_location="./text/dict.txt", user_stopwords_location="./text/stopwords.txt"):
        self.user_dict_location = user_dict_location
        self.user_stopwords_location = user_stopwords_location
        #self.add_dict = dict()
        self.gathered_info = []
        # jieba configuration
        jieba.enable_paddle()
        if self.user_dict_location != None and os.path.isfile(self.user_dict_location):
            jieba.load_userdict(user_dict_location)
            print("inf: loaded user dictionary.")

        if self.user_stopwords_location != None and os.path.isfile(self.user_stopwords_location):
            tmp_file = open(pathlib.Path(self.user_stopwords_location))
            for line in tmp_file:
                line = line.strip()
                line = line.rstrip(os.linesep)
                self.stopwords_list.append(line)
            print("inf: loaded stop words.")

    #-------------------x train x---------------------

    def generate_match_list(self, tree, parent_list):
        '''
        return:
            [
                {
                    "name":"xxx",
                    "parent":[main, node1, subnode1],
                    "text_dir":"/path/text/",
                    "list_match_text":[ [file1],[file2] ... ]
                },
                ...
            ]
        '''
        if tree.list_of_child_nodes == []:
            # only cares about stubs
            add_dict = dict()
            add_dict["name"] = tree.name
            add_dict["parent_list"] = parent_list
            add_dict["text_dir"] = os.path.join(tree.text_path,tree.name)
            add_dict["list_match_text"] = self.dir_to_list_list(add_dict["text_dir"])
            # ^^^-- [ [1.txt], [2.txt] ... ] with dir_to_list_list()
            self.gathered_info.append(add_dict)
        else:
            parent_list_copy = deepcopy(parent_list)
            parent_list_copy.append(tree.name)

            for node in tree.list_of_child_nodes:
                self.generate_match_list(node, parent_list_copy)


    #-------------------x private x---------------------

    def file_to_list_seglist(self, path_to_file):
        '''
        removes stopwords
        return:
            each line to a list
            [
                [ "this", "is", "the", "first", "line" ],
                [ "this", "is", "the", "second", "line" ],
                ...
            ]
        '''
        ret_list = []
        t_file = open(path_to_file,"r")
        for line in t_file:
            line = line.strip()
            if len(line) == 0:
                continue

            list_of_words = jieba.cut_for_search(line)
            list_of_words = list(filter(lambda a: a != ' ', list_of_words)) # remove all spaces
            ret_list.append([word for word in list_of_words if word not in self.stopwords_list])
        
        t_file.close()
        return ret_list

    def file_to_list(self, path_to_file):
        '''
        return:
            [ "all", "lines", "in" , "a", "file" ]
            it's a single array
        '''
        data_file_path = path_to_file
        all_seg_list = self.file_to_list_seglist(data_file_path)
        ret_list = []
        for seg_list in all_seg_list:
            ret_list += seg_list
        return ret_list

    def dir_to_list_list(self, path_to_dir):
        '''
        return: [
            ["list", "from", "file 1"],
            ["list", "from", "file 2"]
            ]
        this list of lists correspondes to a product
        '''
        if not os.path.isdir(path_to_dir):
            return None

        ret_list = []
        for t_file in os.listdir(path_to_dir):
            if t_file.endswith(".txt"):
                open_path = os.path.join(path_to_dir, t_file)
                t_file_content = self.file_to_list(open_path)
                ret_list.append( t_file_content )

        return ret_list

