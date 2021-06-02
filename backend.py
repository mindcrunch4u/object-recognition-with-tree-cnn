#!/usr/bin/env python
import os
import sys
from copy import deepcopy

from components.utils import bracket_check, generic_print, err, ok, inf, debug, pack_details_dict, save_pickle, load_pickle
from components.node import node, init
from components.config_loader import load_tree, load_global_config
from components.move import recover_moved_files
import json
import fnmatch
from prettytable import PrettyTable

def configure_tree_with_global_config(tree, config_dict):
    try: # try, incase load_global_config() fails to pack the dictionary
        is_train_cnn_tree = False
        is_train_text_tree = False

        if config_dict["train_cnn_tree"] != None: 
            if config_dict["train_cnn_tree"] == '1':
                is_train_cnn_tree = True

        if config_dict["train_text_tree"] != None:
            if config_dict["train_text_tree"] == '1':
                is_train_text_tree = True

        tree.configure(is_train_cnn_tree, is_train_text_tree)
    except:
        pass
    return tree

def preprop():
    #TODO pre-processing(): crop and pad images
    pass

def preprop_text():
    #TODO pre-processing-text(): remove unnecessary parts from text, e.g. <body> etc.
    pass

def count_files(dir):
    return len([1 for x in list(os.scandir(dir)) if x.is_file()])

def balance_check( tree, parent_path=[], pretty_table=None ):
    #balance_check():  given a tree, check image data balance for each level
    if pretty_table == None:
        pretty_table = PrettyTable(["INSIDE","NODE NAME","COUNT"])
    total = 0
    if tree.list_of_child_nodes == []:
        #stub
        if tree.images_path == '' and tree.images_path == None:
            return 0
        else:
            real_path = os.path.join(tree.images_path, tree.name)
            return count_files(real_path)

    #check node itself
    result_dict = dict()
    result_dict["name"] = tree.name
    result_dict["value"] = 0
    parent_path_copy = deepcopy(parent_path)
    parent_path_copy.append(tree.name)
    if tree.images_path != '' and tree.images_path != None:
        real_path = os.path.join(tree.images_path, tree.name)
        node_itself_count = count_files(real_path)
        result_dict["name"] = tree.name
        result_dict["value"] = node_itself_count

    result_list = []
    #check nodes children
    for node in tree.list_of_child_nodes:
        value = balance_check( node, parent_path_copy, pretty_table )
        name = node.name
        result_list.append({"name":name,"value":value})

    for item in result_list:
        pretty_table.add_row([parent_path_copy, item["name"], item["value"]])
    pretty_table.add_row(["---LEV---","---LEV---","---LEV---"])

    result_list.append(result_dict) # append images under this node, along with its children's

    for item in result_list:
        try:
            total += item["value"]
        except:
            pass

    return total


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print("Usage: backend -[init|check|train|train-text]")
        print("\t-init: initialize directories based on models.conf")
        print("\t-check: check if training images are balanced, and if nodes are complete")
        print("\t-train: train Tree-CNN using models.conf")
        print("\t-train-text: train a text classifier using text.conf")
        sys.exit(0)

    config_dict = load_global_config("./global.conf")

    if sys.argv[1] == '-init':
        parsed_tree_saved_at = config_dict["parsed_tree_saved_at"]
        tree = load_tree("./models.conf")
        tree = configure_tree_with_global_config(tree, config_dict)

        if config_dict["models_tree_path"] != None:
            init( tree, config_dict["models_tree_path"] )
        else:
            init( tree )

        stat = tree.stub_check()
        save_pickle(tree, parsed_tree_saved_at)
        inf("Parsed tree saved at: "+parsed_tree_saved_at)

    elif sys.argv[1] == '-train-text':
        from text.text import text
        parsed_tree_saved_at = config_dict["parsed_tree_saved_at"]
        if not os.path.isfile(str(parsed_tree_saved_at)):
            err("parsed model tree not found. run -init first: "+parsed_tree_saved_at)
            sys.exit(1)

        tree = load_pickle(parsed_tree_saved_at)
        stat = tree.stub_check()
        print("Tree Status: ",stat)
        if not stat:
            err("make sure each stub is configured and try again.")
            sys.exit(1)

        text_model = text(config_dict["user_dict_saved_location"])

        # training text matcher
        text_model.generate_match_list(tree, [])
        info = text_model.gathered_info

        text_dict_saved_location = config_dict["text_dict_saved_location"]
        save_pickle(info, text_dict_saved_location)
        print("Text matching dictionary saved to: " + text_dict_saved_location)

    elif sys.argv[1] == '-train':
        parsed_tree_saved_at = config_dict["parsed_tree_saved_at"]
        if not os.path.isfile(str(parsed_tree_saved_at)):
            err("parsed model tree not found. run -init first: "+parsed_tree_saved_at)
            sys.exit(1)

        tree = load_pickle(parsed_tree_saved_at)
        tree = configure_tree_with_global_config(tree, config_dict)
        stat = tree.stub_check()
        print("Tree Status: ",stat)
        if not stat:
            err("make sure each stub is configured and try again.")
            sys.exit(1)
        inf("Loading TF Modules. Please standby...")
        from ml_cnn.train_cnn_tree import train_tree
        # [sofa, curtains] --> prediction [0] --> sofa
        # [sofa, curtains] --> prediction [1] --> curtains
        # BEWARE! order of classes matters

        all_models_path = config_dict["models_tree_path"]
        if all_models_path == None:
            all_models_path = "all_models" # default models directory

        train_tree( tree, all_models_path )
        # right_stub might point to the directory of left_stub

    elif sys.argv[1] == '-check':
        parsed_tree_saved_at = config_dict["parsed_tree_saved_at"]
        if not os.path.isfile(str(parsed_tree_saved_at)):
            err("parsed model tree not found. run -init first: "+parsed_tree_saved_at)
            sys.exit(1)

        tree = load_pickle(parsed_tree_saved_at)
        tree = configure_tree_with_global_config(tree, config_dict)
        tree.print()
        stat = tree.stub_check()
        print("Tree Status: ",stat)
        if stat:
            pretty_table = PrettyTable(["INSIDE","NODE NAME","COUNT"])
            total_images = balance_check( tree, [], pretty_table )
            print("Total images: ", total_images)
            print(pretty_table)

    else:
        print("argument not understood.")

