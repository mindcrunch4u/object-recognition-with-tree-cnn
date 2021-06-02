from components.node import node
from components.utils import debug, inf
from components.move import move_to, move_fro, recover_moved_files
from ml_cnn.fit_model import fit_model
import os

'''
E.g. all models are saved in all_models/
train_tree(tree, "all_models/")

then:
    all_models/
    ├── dir-another
    │   └── mod-another.h5  <-- model under its directory
    ├── dir-main
    │   └── mod-main.h5
    └── mod-universe.h5     <-- king of all
'''

def train_tree(tree, save_parent_dir):
    # skip stub
    if tree.list_of_child_nodes == []:
        #this is a stub
        return
    # go up
    
    for node in tree.list_of_child_nodes:
        train_tree(node, os.path.join(save_parent_dir,"dir-"+tree.name))
        '''
        after one node is done training, if the calling node is "universe"
          then the just-trained node is a top-level node
          to avoid untrained node's stub pointing to trained stub,
          whose images are moved to its parent
          recover the images at this point
        '''

    list_of_child_nodes = sorted(tree.list_of_child_nodes, key=lambda x: x.name)
    # sort nodes by name, so that the predictions can be easily interpreted:
    # [0] --> sorted_nodes[0]

    training_list_dict = list()
    for node in list_of_child_nodes:
        # [{name: node.name , path: node.path}, ... ]
        t_dict = dict()
        t_dict["name"] = node.name
        t_dict["path"] = node.images_path #<-- corresponding directory can be found under this dir
        training_list_dict.append(t_dict) #<-- ordered storage

    model_save_path = os.path.join(save_parent_dir, "mod-"+tree.name+".h5")
    train_path_list = []
    train_class_list = []
    for t_dict in training_list_dict:
        train_class_list.append(t_dict["name"])
        train_path_list.append(t_dict["path"])

    train_path_list = list(dict.fromkeys(train_path_list))

    inf("Calling train from: "+tree.name)
    inf("using folder(s): "+', '.join(train_path_list))
    inf("training class(es): "+' ,'.join(train_class_list))
    inf("saving to: "+model_save_path)
    # train (this)upper node
    fit_model(train_path_list, train_class_list, model_save_path)

    if tree.name == "universe":
        # reached top level node
        recover_moved_files(tree)
        return

    # if it's still not "universe", move files from child to self
    print("Moving files, please standby...")
    for t_dict in training_list_dict:
        from_child_path = os.path.join(t_dict["path"],t_dict["name"])
        to_parent_path = os.path.join(tree.images_path, tree.name)
        move_to(from_child_path, to_parent_path)

    return # move back up
'''

-----------------------MODEL
universe
main,
    chair,
        model a
        model b
    curtains

-----------------------TRAINING
training:
    -x- model a  <-- skip stubs
    -x- model b  <-- skip
    chair: [model a, model b]
    ; move model a, model b images up under chair
    -x- curtains <-- skip
    main: [chair, curtains]
    ; move chair images up under main
    ; move curtains images up under main

    first train child
    if not train or child done training:
        move child's images up under parent
        recursive --> train parent

-----------------------FILENAME
    During moving:
        rename if the name exist, until no matches
        record: { rand_IMG_1.jpg : IMG_1.jpg } <-- in_parent : in_child

        generate child's files move_record.pickle on the go
        
        !
        do not move description.txt <-- used in train_text_tree
        do not move move_record.pickle

    After training:
        any file from move_record.pickle will be
        sent back down to child's folder
        rename referencing "record"

    E.g.
        *child to parent*
        IMG_1.jpg
        41_IMG_1.jpg    <-- { "41_IMG_1.jpg" : "IMG_1.jpg" }
        52_41_IMG_1.jpg

        *parent to child*
        52_41_IMG_1.jpg <-- { "52_41_IMG_1.jpg": "41_IMG_1.jpg" }
        41_IMG_1.jpg
        IMG_1.jpg

'''

