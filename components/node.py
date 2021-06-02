import os
from copy import deepcopy
from components.utils import bracket_check, generic_print, err, ok, inf, debug, strip_list

class node:
    name = ''
    images_path = '' # <-- its parent folder
    # os.path.join(images_path,self.name) <-- the actual folder
    text_path = ''
    list_of_child_nodes = []
    is_train_images=True
    is_train_text=True
    def __init__(self, name):
        self.images_path = ''
        self.text_path = ''
        self.list_of_child_nodes = []
        self.name = name
        self.images_count = 0
    def configure(self, _is_train_images, _is_train_text):
        node.is_train_images = _is_train_images
        node.is_train_text = _is_train_text
    def set(self, _images_path, _text_path):
        # if there won't be any text/image for this model, 
        # then point to an empty directory.
        self.images_path = _images_path
        self.text_path = _text_path


    def add(self, node_path, stub_info): # "stub_info" is a dict, which contains image path etc.
        # entry point for adding node path
        # dispatched to add_list() when list length > 1
        if bracket_check(node_path):
            node_path = node_path.split('[')[1].split(']')[0]
            node_list = node_path.split(',')
            node_list = strip_list(node_list)
            if len(node_list) == 0:
                return True

            found_node = self.fetch_childnode_by_name(node_list[0])
            working_subtree = None
            if found_node == None:
                new_subtree = node(node_list[0])
                self.list_of_child_nodes.append(new_subtree)
                working_subtree = new_subtree
                debug("creating "+str(working_subtree.name))
            else:
                working_subtree = found_node
                debug("retrieved "+str(working_subtree.name))

            stub = None
            if len(node_list) == 1:
                # end of list, stub is self
                #return True
                stub = working_subtree
            else:
                stub = working_subtree.add_list(node_list[1:]) # recursive

            try:
                stub.set(stub_info['img_dir'],stub_info['txt_dir'])
                debug("stub info added to: "+stub.name)
            except:
                debug("missing stub info for node: " + str(stub.name)+", skipped.")
                
            return True
        else: # malformed model path
            return False
            
    def add_list(self, node_path_list):
        debug("descended into: "+str(self.name))
        found_node = self.fetch_childnode_by_name(node_path_list[0])
        working_subtree = None
        if found_node == None:
            new_subtree = node(node_path_list[0])
            self.list_of_child_nodes.append(new_subtree)
            working_subtree = new_subtree
            debug("creating "+str(working_subtree.name))
        else:
            working_subtree = found_node
            debug("retrieved "+str(working_subtree.name))


        if len(node_path_list) == 1:
            # end of list
            #return self
            return working_subtree
        else:
            return working_subtree.add_list(node_path_list[1:]) # recursive
        pass
        
    def fetch_childnode_by_name(self, name):
        for subnode in self.list_of_child_nodes:
            if subnode.name == name:
                return subnode
        return None
        
    def print(self, indent=0):
        for node in self.list_of_child_nodes:
            print(' '*indent+ node.name+',')
            if self.is_train_images:
                if node.images_path != None:
                    print(' '*indent+ "`Image dir: "+str(os.path.join(node.images_path,node.name)))
                else:
                    print(' '*indent+ "`Image dir: "+"None")
            if self.is_train_text:
                if node.text_path != None:
                    print(' '*indent+ "`Texts dir: "+str(os.path.join(node.text_path,node.name)))
                else:
                    print(' '*indent+ "`Texts dir: "+"None")
            node.print(indent+2) # recursive
            
    def stub_check(self, parent_list=[]):
        parent_list_copy = deepcopy(parent_list) # deepcopy to pass-by-value
        parent_list_copy.append(self.name) # include parent list for reporting misconfigured nodes

        # check if each stub has images directory set up
        # this have to return True before training
        is_stub_filled = True
        if len(self.list_of_child_nodes) == 0:
            # this is a stub
            parent_string = "-> ".join(parent_list_copy)
            if node.is_train_images:
                if self.images_path == None or self.images_path == '' or not os.path.isdir(self.images_path):
                    err("Stub: "+parent_string+", lacks images directory. Misconfigured or non-exist.")
                    is_stub_filled = False
            if node.is_train_text:
                if self.text_path == None or self.text_path == '' or not os.path.isdir(self.text_path):
                    err("Stub: "+parent_string+", lacks text directory. Misconfigured or non-exist.")
                    is_stub_filled = False
            return is_stub_filled

        for subnode in self.list_of_child_nodes:
            if not subnode.stub_check( parent_list_copy ):
                is_stub_filled = False

        # check the stub(parent) itself
        if self.name != "universe":
            parent_string = "-> ".join(parent_list_copy)
            if self.is_train_images:
                if self.images_path == None or self.images_path == '' or not os.path.isdir(self.images_path):
                    err("Stub: "+parent_string+", lacks images directory. Misconfigured or non-exist.")
                    is_stub_filled = False
            if self.is_train_text and len(self.list_of_child_nodes) == 0:
                # NOTE only check stubs when training text-matching component
                if self.text_path == None or self.text_path == '' or not os.path.isdir(self.text_path):
                    err("Stub: "+parent_string+", lacks text directory. Misconfigured or non-exist.")
                    is_stub_filled = False

        return is_stub_filled # True:ok, False:bad


def init( tree, models_main_directory='./modelstree' ): 
    # replace './modelstree' with the setting in global.conf

    # creates directoriy tree for models tree
    # creates directoriy tree for nodes' images
    # creates text file for each node

    # creating directories for models
    new_parent_dir = str(os.path.join(models_main_directory,"dir-"+tree.name))
    os.makedirs(new_parent_dir, exist_ok=True)

    # not creating "universe" data directory, cause it uses its sub directory to train
    #   and it's the first classifier if need be.

    for node in tree.list_of_child_nodes:
        #mkdir for images directories, and touch for text files
        if node.is_train_images and (node.images_path != None and node.images_path != ''):
            path_with_node_name = os.path.join(node.images_path, node.name)
            t_directory = os.path.abspath(path_with_node_name)
            os.makedirs(t_directory, exist_ok=True)
        if node.is_train_text and (node.text_path != None and node.text_path != ''):
            path_with_node_name = os.path.join(node.text_path, node.name)
            t_directory = os.path.abspath(path_with_node_name)
            os.makedirs(t_directory, exist_ok=True)

        new_parent_dir_copy = deepcopy(new_parent_dir)
        init( node, new_parent_dir_copy )


class balance_node:
    list_of_child_nodes = []
    image_count = 0
    def __init__(self):
        self.list_of_child_nodes = []
        self.dict_nodes_images_count = dict()
        self.image_count = 0

#TODO balance check
def balance_check(tree, b_node):
    # travese tree, fill in b_node
    # b_node : in-place changing
    pass
