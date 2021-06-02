# move files from child directory to parent's directory
# leaving a record in parent's directory (for calling move_fro in parent's directory)
# TODO: implement move_one_file_to() to move text file between each directory

'''
Example:

    one-to-one

    move_to( 1, 2 )
    move_to( 2, 3 )

    move_fro( 3, 2 )
    move_fro( 2, 1 )

    or many-to-one

    move_to( a, dest )
    move_to( b, dest )

    move_fro( dest, a )
    move_fro( dest, b )

    TL;DR: everything looks the same,
    except dest folder has an extra record.pickle

    BEWARE:
    remove the record, after all files are moved back
    so that there won't be any rubbish in the record

'''


from components.utils import save_pickle, load_pickle, debug, err
import os
import shutil

def recover_moved_files( tree, record_dict_name="record.pickle" ):

    is_skip_moving = False
    if tree.name == "universe": 
        # universe won't possibly have any data, so skip
        # avoid touching it's unset "images_path"
        is_skip_moving = True

    if not is_skip_moving:
        tree_pickle_path = os.path.join(tree.images_path, tree.name, record_dict_name)
        if os.path.isfile(tree_pickle_path):
            print("Found record for node: "+tree.name+", at: "+tree_pickle_path)
            from_path = os.path.join(tree.images_path, tree.name)
            for child in tree.list_of_child_nodes:
                back_to_path = os.path.join(child.images_path, child.name)
                print("Move to: "+back_to_path)
                move_fro(from_path, back_to_path)
            #done moving, remove record
            os.remove(tree_pickle_path)
            print("record for node: "+tree.name+", removed")

        pass 

    for node in tree.list_of_child_nodes:
        recover_moved_files(node, record_dict_name)

    #   yes, gather name, and move_fro
    #   
    #   for node in tree.list_of_child_nodes:
    #       recover_moved_files( node, record_dict_name )
    # move_fro( parent, child )
    # remove record
    pass

def move_to( from_dir, to_dir, record_dict_name="record.pickle" ):
    is_error_found = False
    # reject non-directory parameters
    if not os.path.isdir(from_dir):
        is_error_found = True
        err("move_to: from directory not exist: "+from_dir)
    if not os.path.isdir(to_dir):
        is_error_found = True
        err("move_to: to directory not exist: "+to_dir)

    if is_error_found:
        return False

    debug("Moving files from: "+from_dir+", to: "+to_dir)

    # try to load existed pickle
    # e.g.  move_to(a, new)
    #       move_to(b, new) <-- shouldn't overwrite the record
    try_pickle_path = os.path.join(to_dir, record_dict_name)
    record = load_pickle(try_pickle_path)
    if record == None:
        # only remove the record
        # when all files are moved back to their original directories
        record = dict()
    '''
    record.pickle{
        is_moved = False,
        from_dir = "",
        to_dir = "",
        name_map = {
            "moved_file_a.jpg" : "file_a.jpg",
            "moved_file_b.jpg" : "file_b.jpg"
        }
    }
    '''
    destination_filenames = []
    for filename in os.listdir(to_dir):
        destination_filenames.append(filename)

    # gather all files in current dir
    source_filenames = []
    dir_iterator = os.scandir(from_dir)
    for entry in dir_iterator:
        if entry.name == record_dict_name or entry.is_dir():
            continue
        if entry.is_file():
            source_filenames.append(entry.name)

    for source_file in source_filenames:
        from_path = os.path.join(from_dir, source_file)
        move_filename = source_file
        is_move_filename_ok = False

        while not is_move_filename_ok:
            is_match_found = False
            # look for overlapping names in destination_filenames
            for dest_file in destination_filenames:
                if move_filename == dest_file:
                    is_match_found = True
                    # found a match, rename source file
                    # TODO? "_" + move_filename, "_" can be a single rand digit
                    move_filename = "_" + move_filename
            # look for overlapping names in record
            for record_file in record:
                if record_file == move_filename:
                    is_match_found = True
                    move_filename = "_" + move_filename

            if not is_match_found:
                is_move_filename_ok = True

        record[move_filename] = from_path # keep a record of all moved files
        to_path = os.path.join(to_dir, move_filename)
        shutil.move(from_path, to_path)

    # except record.pickle
    # move each to parent, check name and record
    # save record.pickle in parent dir
    save_path = os.path.join(to_dir,record_dict_name)
    save_pickle( record, save_path )
    return True


# move files back from parent directory to child directory
def move_fro( from_dir, back_to_dir, record_dict_name="record.pickle" ):
    is_error_found = False
    if not ( os.path.isdir(from_dir) and os.path.isdir(back_to_dir) ):
        # reject non-directory parameters
        err("move_fro: parameter(s) not directories or not exist.")
        is_error_found = True

    save_path = os.path.join(from_dir, record_dict_name)
    record = load_pickle(save_path)
    if record == None: # make sure record file exists
        err("mov_fro: missing file list: "+record_dict_name)
        is_error_found = True
    if is_error_found:
        return
    
    debug("Moving files from: "+from_dir+", back to: "+ back_to_dir)

    from_dir_files = []
    for filename in os.listdir(from_dir):
        if filename == record_dict_name:
            continue
        from_dir_files.append(filename)

    for filename in from_dir_files:
        try:
            original_name = record[filename] # there is an record, aka. the file belongs somewhere else
            if back_to_dir == os.path.dirname(original_name): # if back_to_dir is its original owner
                back_to_path = original_name
                from_path = os.path.join(from_dir, filename)
                shutil.move(from_path, back_to_path)
        except:
            # not one of the moved files
            continue

    pass
