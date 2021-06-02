import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # FATAL
import tensorflow as tf
from tensorflow.keras import datasets, layers, models
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Conv2D, Flatten, Dropout, MaxPooling2D
from PIL import Image
from skimage import transform
import numpy as np
import sys
import pathlib

from components.utils import inf, err, debug

#classes_placeholder = [ "class 1" , "class 2" ]

_IMAGE_HEIGHT=32
_IMAGE_WIDTH=32
_BATCH_SIZE=32
_SCALE=255
_TRAIN_EPOCH=9

class CombinedGen():
    def __init__(self, list_of_gens):
        self.gens = tuple(list_of_gens)

    def generate(self):
        while True:
            for g in self.gens:
                yield next(g)

    def __len__(self):
        return sum([len(g) for g in self.gens])

def load_config_from_dict(config_dict):
    if config_dict == None:
        return

    global _IMAGE_HEIGHT
    global _IMAGE_WIDTH
    global _BATCH_SIZE
    global _SCALE
    global _TRAIN_EPOCH
    try:
        _IMAGE_HEIGHT = config_dict["_IMAGE_HEIGHT"]
    except:
        pass
    try:
        _IMAGE_WIDTH = config_dict["_IMAGE_WIDTH"]
    except:
        pass
    try:
        _BATCH_SIZE = config_dict["_BATCH_SIZE"]
    except:
        pass
    try:
        _SCALE = config_dict["_SCALE"]
    except:
        pass
    try:
        _TRAIN_EPOCH = config_dict["_TRAIN_EPOCH"]
    except:
        pass
    

# list: tmp_train_dir_path, 
# list: classes_placeholder, 
# string: model_save_as, 
# dict: config_dict
def fit_model( tmp_train_dir_path, classes_placeholder, model_save_as, config_dict=None ): 

    load_config_from_dict( config_dict )
    _CLASS_COUNT = len(classes_placeholder)
    model = None

    is_directory_missing = False
    for each_dir in tmp_train_dir_path:
        if not os.path.isdir( each_dir ):
            err("missing training directory: "+str(each_dir))
            is_directory_missing = True
    if is_directory_missing:
        return

    list_of_training_gen = []
    list_of_validation_gen = []
    # Iterate through each directory and combine all the images for training
    for each_dir in tmp_train_dir_path:

        data_dir_path = each_dir
        data_dir = pathlib.Path(data_dir_path)
        #image_count = len(list(data_dir.glob('*/*'))) <-- unused

        t_datagen = tf.keras.preprocessing.image.ImageDataGenerator(
            rescale=1./_SCALE,
            shear_range=0.2,
            zoom_range=0.2,
            validation_split=0.2, # for 0.2 and few images, there won't be any for validation left
            # NOTE Image Augmentation Down Below
            horizontal_flip=True,
            rotation_range=30, fill_mode='nearest',
            brightness_range=[0.7,1.3]
        )

        # generate training data
        train_generator = t_datagen.flow_from_directory(directory=str(data_dir),
                                                             batch_size=_BATCH_SIZE,
                                                             shuffle=True,
                                                             color_mode="rgb",
                                                             class_mode="categorical",
                                                             subset="training",
                                                             target_size=(_IMAGE_HEIGHT, _IMAGE_WIDTH),
                                                             classes = list(classes_placeholder))

        list_of_training_gen.append(train_generator)
        debug(train_generator.filenames)

        # generate validation data
        validation_generator = t_datagen.flow_from_directory(directory=str(data_dir),
                                                            batch_size=_BATCH_SIZE,
                                                            shuffle=True,
                                                            color_mode="rgb",
                                                            class_mode="categorical",
                                                            subset="validation",
                                                            target_size=(_IMAGE_HEIGHT, _IMAGE_WIDTH),
                                                            classes = list(classes_placeholder))
        list_of_validation_gen.append(validation_generator)
        debug(validation_generator.filenames)

    # combine all generated data
    training_combined_generator = CombinedGen(list_of_training_gen)
    validation_combined_generator = CombinedGen(list_of_validation_gen)

    # Creating model
    model = models.Sequential()

    COLOR_CHANNELS = 3 # 3 for RGB
    _CLASS_COUNT = len(classes_placeholder)

    model.add(layers.Conv2D(_IMAGE_HEIGHT*1, (3, 3), activation='relu', input_shape=(_IMAGE_HEIGHT, _IMAGE_WIDTH, COLOR_CHANNELS)))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(_IMAGE_HEIGHT*2, (3, 3), activation='relu'))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(_IMAGE_HEIGHT*4, (3, 3), activation='relu'))

    model.add(layers.Flatten())
    model.add(layers.Dense(_IMAGE_HEIGHT*4, activation='relu'))
    model.add(layers.Dense(_CLASS_COUNT, activation='softmax'))

    # Compiling model
    model.compile(optimizer='adam',
                  loss=tf.keras.losses.CategoricalCrossentropy(from_logits=True),
                  metrics=['accuracy'])

    # detect if the generator has no images, avoid messing up the training
    if len(training_combined_generator) <= 0 or len(validation_combined_generator) <= 0:
        print("FATAL: no images for training or validation. Abort training.")
        return

    training_steps_per_epoch = len(training_combined_generator)//_BATCH_SIZE
    if training_steps_per_epoch <= 0:
        training_steps_per_epoch = 1
    validation_steps_per_epoch = len(validation_combined_generator)//_BATCH_SIZE
    if validation_steps_per_epoch <= 0:
        validation_steps_per_epoch = 1

    # Training model
    history = model.fit(
            training_combined_generator.generate(),
            validation_data= validation_combined_generator.generate(),
            #steps_per_epoch = training_steps_per_epoch,
            steps_per_epoch = 10, #TODO figure out what's the best way to set this
            validation_steps = validation_steps_per_epoch,
            epochs= _TRAIN_EPOCH,
            verbose=2
            )

    model.save( model_save_as )
    print("Model Saved: "+model_save_as)

    return True
