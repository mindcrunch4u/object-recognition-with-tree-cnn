
# environment
numpy==1.19.5

# before training
training data used by models are configured in models.conf
trained models' saving location is configured in global.conf

# model's dir
all (trained) models' filenames begin with mod-
all models' directories begin with dir-
e.g.

└── dir-main
    ├── dir-chair
    │   ├── dir-model A <-- a stub won't have its model.
    │   ├── dir-model B
    │   └── mod-chair.h5 <-- chair's CNN model
    └── mod-main.h5 <-- main's CNN model

# h5py
models are saved using h5py.

# interruption
If the training process was interrupted, there might be orphaned files.
(orphaned files: files not in their original directories)
Moving files back to where the belong is yet to be implemented, it can be easily done by using method `move_to()` and `move_fro()`


# pain matching vs machine learning

Product descriptions are rare, that means there won't be enough data for machine learning.
While texts near(or on) the products are limited and fixed, plain matching would do the trick.
Therefore for each product there will be a structure as:

    product_name
    [ text_list_1, text_list_2, ... ]

where text_list is the content of one chunck of text near(or on) the product.
