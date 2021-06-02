import os
import sys
from components.utils import bracket_check, generic_print, err, ok, inf, debug, pack_details_dict
from components.node import node

# handles models.conf and global.conf

# loads from models.conf, display any error within the config
# returns the loaded tree, without any guarentee that the tree works
# check the tree before using it

def load_tree( path_to_config ):
    inf("parsing starts.")
    if os.path.isfile( path_to_config ):
        inf("models config located.")
    else:
        err("models config missing, abort.")
        return None
    models_conf = open(path_to_config, 'r')

    look_for_end_of_comment = False

    # parsing models tree
    is_bad_line_found = False
    tree = node("universe")
    cleaned_lines = []
    for line in models_conf:
        line = line.split(';')[0].strip()
        if len(line) == 0:
            continue
        cleaned_lines.append(line)

    line_index = -1
    for line in cleaned_lines:
        line_index += 1
        stub_info = []
        if line[0] == '[' and bracket_check( line ): # found [] bracket config
            # handle additional information under a bracket
            try:
                for details in cleaned_lines[line_index+1:]:
                    if not (details[0] == '[' and bracket_check( details )):
                        # append anything until another config bracket is found
                        stub_info.append(details)
                    else:
                        break
            except:
                pass # reached end of list
            stub_info = pack_details_dict(["img_dir","txt_dir"], stub_info)
            status = tree.add(line, stub_info)
            if not status:
                is_bad_line_found = True
                err("bad config found under line: "+str(line))
        elif line[0] == '[' and not bracket_check( line ):
            is_bad_line_found = True
            err("malformated config bracket found at line: "+str(line))
        else:
            pass # passing detail lines

    if is_bad_line_found:
        err("fix models config and try again. Abort.")
        return -1

    models_conf.close()
    return tree

def load_global_config( path_to_config ):
    if not os.path.isfile( path_to_config ):
        inf("global config missing.")
        return None
    global_conf = open( path_to_config, 'r' )

    cleaned_lines = []
    for line in global_conf:
        line = line.split(';')[0].strip()
        if len(line) == 0:
            continue
        cleaned_lines.append(line)
    required_list = ["debug_level","error_level",
            "log","inbalance_warning","train_cnn_tree",
            "train_text_tree","prepro_height","prepro_width","models_tree_path",
            "text_dict_saved_location","parsed_tree_saved_at","user_dict_saved_location"]
    ret_dict = pack_details_dict(required_list, cleaned_lines)
    global_conf.close()
    return ret_dict
