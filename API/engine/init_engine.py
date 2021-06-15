from engine.predictor import predictor
from pathlib import Path
import os

def get_predictors_list(read_models_id_dir):
    # returns { "model_id":"furnitures", "predictor":Obj_Predictor }
    # TODO configure predictor's user_dict
    ret_list = list()
    read_models_id_dir = Path(read_models_id_dir)
    for lsdirs in os.listdir(read_models_id_dir):
        predictor_model_id = lsdirs
        predictor_match_dict = os.path.join(read_models_id_dir, lsdirs,'match_dict.dat')
        predictor_image_dir  = os.path.join(read_models_id_dir, lsdirs)
        tmp_predictor = predictor(path_to_cnn_tree_folder=predictor_image_dir, path_to_match_dict=predictor_match_dict)
        tmp_dict = {"model_id":predictor_model_id, "predictor":tmp_predictor}
        print("LOADED: ", tmp_dict)
        ret_list.append(tmp_dict)
    return ret_list
