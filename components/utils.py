import os
import pickle

is_using_log_file = False
log_path = './file.txt'
debugging_level = 3
error_level = 0

def strip_list(input_list):
    index = 0
    for item in input_list:
        item = str(item)
        input_list[index] = item.strip()
        index += 1
    return input_list

def bracket_check( line ):
    if line.count('[') == 1 and line.count(']') == 1\
            and line[0] == '[' and line[-1] == ']':
        return True
                
def generic_print( tag, str_message ):
    global is_using_log_file
    global log_path
    # log error
    tag = '['+str(tag)+']'
    if is_using_log_file:
        if os.path.isfile( log_path ):
            # write
            f = open( log_path, 'a' )
            f.write( tag+' ' )
            f.write( str_message )
            f.write( "\n" )
            f.close()
        else:
            print(tag, str_message) # fallback to stdout
    else:
        print(tag, str_message)

def err( str_message, level=0 ):
    if level >= error_level:
        generic_print('err', str_message)

def ok( str_message ):
    generic_print('ok',str_message)

def inf( str_message ):
    generic_print('info',str_message)

def debug( str_message, level = 0 ):
    if level >= debugging_level:
        generic_print(str(level)+'-debug',str_message)


def pack_details_dict(required_list, details_list):
    # required_list : [option1, option2, ...] -- strings
    # details_list: ["option1=value1", "option2=value2"] -- strings
    ret = dict()
    for required_item in required_list:
        ret[required_item] = None # initialize return dict

    details = dict()
    for item in details_list:
        item = item.strip() # ignore prepending/trailing spaces
        to_list = item.split('=')
        if len(to_list) == 0:
            err("invalid config found at line: " + str(item))
        elif len(to_list) == 1 or ( len(to_list) == 2 and len(to_list[1]) == 0 ):
            err("option missing value found at line: " + str(item))
        elif len(to_list) == 2:
            option = to_list[0].strip()
            value = to_list[1].strip()
            if option in required_list:
                ret[option] = value
            else:
                debug("skipping unrequired option:value of: " + str(item))
        else:
            err("malformed config found at line: " + str(item))
    return ret


def save_pickle( obj, save_path ):
    save_path = str(save_path)
    try:
        pickle.dump( obj, open( save_path, "wb" ) )
    except:
        err("save: missing file: "+save_path)
        return None
    return True

def load_pickle( save_path ):
    save_path = str(save_path)
    try:
        obj = pickle.load( open( save_path, "rb" ) )
    except:
        return None
    return obj
