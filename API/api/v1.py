ocr_text_list_item_count_threashold = 10
from __main__ import app
from flask import request, jsonify
from main import conn
from main import shared_predictors_list
from engine.predictor import predictor
from engine.ocr import b64_to_text_list

PREDEF_KEY="abc567"

# id refers to the post_id (within a model/table)

@app.route('/api/v1/is_editor_key_valid')
def is_editor_key_valid():
    result = False
    if 'key' in request.args:
        if str(request.args['key']) == PREDEF_KEY:
            result = True
        else:
            result = False
    return jsonify(result)

@app.route('/api/v1/get_list_of_post')
def api_get_list_of_post():
    ret_list = None
    if 'model_id' in request.args:
        model_id = str(request.args['model_id'])
        ret_list = conn.get_list_of_post_by_model_id(model_id)
    return jsonify(ret_list)

@app.route('/api/v1/get_list_of_model_id')
def api_get_list_of_model_id():
    ret_list = conn.get_list_of_model_id()
    return jsonify(ret_list)

@app.route('/api/v1/get_post')
def api_get_post():
    post_id = ""
    ret_dict = dict()
    ret_dict["name"] = None
    ret_dict["content"] = None

    if 'model_id' in request.args and 'id' in request.args:
        model_id = str(request.args['model_id'])
        post_id = str(request.args['id'])
        try:
            # get_result could be None
            get_result = conn.get_post_by_id(model_id, post_id)
            ret_dict["name"] = get_result["name"]
            ret_dict["content"] = get_result["content"]
        except:
            pass

    return jsonify(ret_dict)

@app.route('/api/v1/update_post', methods=['POST'])
def api_update_post():
    ret_dict = dict()
    ret_dict["status"] = False

    if request.json and 'model_id' in request.json and 'id' in request.json and 'content' in request.json and 'key' in request.json:
        model_id = str(request.json['model_id'])
        post_id = str(request.json['id'])
        post_content = str(request.json['content'])
        key = str(request.json['key'])

        ret_dict["status"] = False
        if conn.is_key_valid(key):
            stat = conn.update_post_by_id(model_id, post_id, post_content)
            ret_dict["status"] = stat

    return jsonify(ret_dict)

@app.route('/api/v1/predict', methods=['POST'])
def api_predict():
    ret_dict = dict()
    ret_dict["rate"] = None
    ret_dict["post_id"] = None

    if request.json and 'model_id' in request.json and 'image_b64' in request.json:
        model_id = str(request.json['model_id'])
        image_b64 = str(request.json['image_b64']) 
        image_b64 = image_b64.split(',')  # <-- strip b64 tag "data:image/png;base64,"
        if len(image_b64) > 1: # <-- sloppy code
            image_b64 = image_b64[1]
        else:
            image_b64 = image_b64[0]


        ocr_text_list = b64_to_text_list(image_b64)

        class_fullname = None
        prediction_dict = None

        if len(ocr_text_list) > ocr_text_list_item_count_threashold:
            print("Using text prediction")
            ocr_joined_string = ' '.join(ocr_text_list)
            prediction_dict = get_fullname_by_match_text(model_id, ocr_joined_string)
            if prediction_dict != None:
                class_fullname = prediction_dict["full_name"]
                print("Get: ",class_fullname)
            else:
                print("Didn\'t get name.")
        else:
            print("Using image prediction")
            # image doesn't have much text on it, then use tree-cnn prediction
            prediction_dict = get_fullname_by_predict(model_id, image_b64)
            if prediction_dict != None:
                class_fullname = prediction_dict["full_name"]
                print("Get: ",class_fullname)
            else:
                print("Didn\'t get name.")

        if not class_fullname == None:
            ret_dict["rate"] = str(prediction_dict["rate"])
            ret_dict["post_id"] = str(conn.get_post_id_by_fullname( model_id, class_fullname ))

    return jsonify(ret_dict)


# predict images
def get_fullname_by_predict( model_id, image_b64 ):
    is_predictor_found = False
    ret_dict = dict()
    ret_dict["full_name"] = None
    ret_dict["rate"] = -1

    for predictor in shared_predictors_list:
        print("Looking for ",predictor["model_id"]," matching: ", model_id)
        if predictor["model_id"] == model_id:
            is_predictor_found = True
            result = predictor["predictor"].recursive_predict_b64(image_b64)
            if result == None:
                return None
            
            # only return dict() when prediction is successful
            ret_dict["full_name"] = result["full_name"]
            ret_dict["rate"] = result["rate"]
            return ret_dict


    if not is_predictor_found:
        return None

# predict text
def get_fullname_by_match_text( model_id, ocr_joined_string ):
    is_predictor_found = False
    ret_dict = dict()
    ret_dict["full_name"] = None
    ret_dict["rate"] = -1

    for predictor in shared_predictors_list:
        print("looking for",predictor["model_id"],", with", model_id, "text: ", ocr_joined_string)
        if predictor["model_id"] == model_id:
            is_predictor_found = True
            result = predictor["predictor"].match(ocr_joined_string)
            if result == None:
                return None
            
            # only return dict() when prediction is successful
            ret_dict["full_name"] = result["full_name"]
            ret_dict["rate"] = result["rate"]
            return ret_dict


    if not is_predictor_found:
        return None
