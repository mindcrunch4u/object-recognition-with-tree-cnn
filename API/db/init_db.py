import os

def clean_appending_dir(fullname_list):
    ret_list = []
    for item in fullname_list:
        ret_list.append( item.replace("dir-","",1) )
    return ret_list

def dir_to_list_of_dict(path_to_model_ids_dir):
    # {"model_id":"furnitures", "fullname":[node1, n2, ...] }
    ret_list = []
    child_dirs_count = 0
    if not os.path.isdir(path_to_model_ids_dir):
        return

    for root, dirs, files in os.walk(path_to_model_ids_dir, topdown=True):
        if not dirs:
            sep_list = root.split(os.sep)
            sep_list.remove(path_to_model_ids_dir)
            sep_list = clean_appending_dir(sep_list)
            tmp_dict = dict()
            tmp_dict["model_id"] = sep_list[0]
            tmp_dict["fullname"] = []
            if len(sep_list) > 1:
                tmp_dict["fullname"] = sep_list[1:]
            ret_list.append(tmp_dict)
    return ret_list


if __name__ == '__main__':
#testing
    get = dir_to_list_of_dict(fixed_models_id_dir)
    for item in get:
        print(item)
