fixed_models_id_dir = 'model_ids' # define shared values (shared between modules)

import flask
import sys
import os
import uuid
from flask import request, jsonify
from db.db import db
from engine.predictor import predictor
conn = db()

from db.init_db import dir_to_list_of_dict
#from prettytable import PrettyTable
from engine.predictor import predictor
from engine.ocr import b64_to_text_list
from engine.init_engine import get_predictors_list

app = flask.Flask(__name__)
app.config["DEBUG"] = True

# predictors init
shared_predictors_list = get_predictors_list(fixed_models_id_dir)

import api.info
import api.v1


def init_db( models_id_dir=fixed_models_id_dir ):
    #pretty_table = PrettyTable(["TABLE/ENGINE_ID", "FULL NAME","POST_ID","STAT"])
    get_list_of_stubs = dir_to_list_of_dict(models_id_dir)
    for stub in get_list_of_stubs:
        # self-defined rule: fullname should be unique, also post_id
        if not conn.is_fullname_exist(stub["model_id"], stub["fullname"]):
            post_id = str(uuid.uuid1())
            # empty content(description) by default
            conn.create_post_by_id(stub["model_id"], post_id, "/".join(stub["fullname"]), stub["fullname"], '')
            print(stub["model_id"], stub["fullname"], post_id, "OK")
            #pretty_table.add_row(stub["model_id"], stub["fullname"], post_id, "OK")
    #print(pretty_table)

    conn.update_post_by_id("furnitures",'7d2463dd-906e-11eb-bf16-080027529c2d', "skdfaskdfaksdbfjkhb")


if __name__ == '__main__':
    if not os.path.isdir( fixed_models_id_dir ):
        print("err: fatal error, directory not found:",fixed_models_id_dir)
        sys.exit(1)
    init_db( fixed_models_id_dir )
    app.run(host='0.0.0.0',port=5000,debug=True)
