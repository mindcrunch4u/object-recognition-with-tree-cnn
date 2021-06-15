
# Environment
```
numpy==1.19.5
```

Newer numpy versions might not be supported.

Check `environment.yml` for conda configuration.

# Before Training

### Know the routine

1. prepare your data

2. edit `models.conf` and `global.conf`

   `models.conf` contains the tree structure and each nodes' image data.

   `global.conf` specifies where to save the trained tree-cnn model.

3. init the training with

   ```
   python3 ./backend.py -init
   ```

   This will create and load a tree structure (filling the tree with nodes and image paths), which can be used for the training. This tree structure can also be used to train a tree-cnn model on another machine.

4. check your configuration with

   ```
   python3 ./backend.py -check
   ```

   Make sure each parent node's child nodes share the same amount of images (like in training a single CNN model, each class is supposed to have the similar amount of images.)

5. train and deploy on server

   ```
   python3 ./backend.py -train #trains the tree-CNN
   python3 ./backend.py -train-text #trains a text-matching dictionary
   ```

   The trained tree-CNN model is by default saved at `./all_models`.

   The text-matching dictionary is by default named `match_dict.dat`.

   Move `match_dict.dat` into folder `./all_models`. Rename `./all_models` if needed, say, to `tree_model_1`. Move this combined folder `tree_model_1` to `/path/to/API/model_ids/` on the server, where multiple tree-CNN models could be hosted.

   Finally start the server with

   ```
   python3 /path/to/API/main.py
   ```

6. spin up the server

   Edit file `/path/to/API/engine/ocr.py`, change the OCR API to your provider with your key.
   
   
   
   ```
   python3 /path/to/API/main.py
   ```

## Preparing your data

Let's say a tree looks something like this:

```
A
└── A 1
└── A 2
B
```

(That's 2 parent nodes `A`, `B`. With node `A` having children `A 1` and `A 2`.)

Then the `models.conf` should look like

```
[A]
[A, A 1]
[A, A 2]
[B]
```

The above configuration is incomplete, but you get the idea -- left bracket, parent node(s), child node, right bracket -- that's how we create a tree with a text file.

The complete configuration looks something like this:

```
[A]
	img_dir = ./photos/	   ; <-- img_dir is mandatory for all nodes.
[A, A 1]
	img_dir = ./photos/
	txt_dir = ./text_data/ ; <-- txt_dir is mandatory for stubs.
[A, A 2]
	img_dir = ./photos/
	txt_dir = ./text_data/
	; text files are expected to be available under "./text_data/A 2/"
[B]
	img_dir = ./bilder/
	; images are expected to be available under ./bilder/B/
```

### Why text?

You might ask "What's the use of text for a image-recognition model?"

Allow me to answer with this question "How could a CNN model possibly tell a **large white napkin** from a **small white napkin** having the same shape?" Well, the answer is "not likely." However with the help of some additional information, say, some text (printed on the packaging or a tag on the shelf) , a machine can easily identify what that item is.

And that's why we need text data: The server does and OCR upon receiving the image, wenn der Anzahl des Texts reicht, benutzt das System "text matching". If there aren't enough text presented on the image, the system would use tree-CNN for recognition.

### Initialize the tree and Check

Initialize the tree with `python3 ./backend -init` so that the configuration can be done locally, while the training happens remotely -- sync the initialized tree (named `parsed_tree.dat` by default) to server.

Check for data imbalance before training `python3 ./backend -check`.

# Training

After making sure that the `models.conf` is configured, and the training data is all set, run

```
python3 ./backend -train
```

to train a huge tree-CNN model. The trained model is by default saved to `./all_models`. The structure of the folder `./all_models` is explained as below:

- each single CNN model, corresponding with a single node, begins with `mod-`, and ends with the node's name. (each CNN model is saved in `h5` format, using `h5py`.)
- children are stored under each nodes' folder, the folder name begins with `dir-`, and ends with the node's name.

Here's an example:

```
./all_models/
└── dir-universe
    ├── dir-chair
    │   ├── dir-chair A <-- a stub is just a folder.
    │   ├── dir-chair B
    │   └── mod-chair.h5 <-- chair's CNN model.
    ├── dir-bottle
    │   ├── dir-bottle A
    │   ├── dir-bottle B
    │   └── mod-bottle.h5 <-- predicts whether an item is of class A or B.
    └── mod-universe.h5 <-- the first CNN model used for prediction.
```

# Oops

If the training was interrupted, there might be `orphaned files`.

`orphaned files`: files not in their original directories. The training module moves data from child nodes to their parent nodes' data folder, in order to train their parent nodes.

Moving files back to where they belong is yet to be implemented, though it can be easily done by using method `move_to()` and `move_fro()`. This would be a bad fix (see TODO).

# Plain matching

Product descriptions, like printed text or price tags, are rare -- that means there won't be enough data for machine learning. However since these descriptions are limited and rather stable, plain matching would do the trick.
So for each product there will be:

    {
    "product_name" : ...,
    "text_list" : [ text_list_1, text_list_2, ... ]
    }

where `text_list` is multiple parts of the product's descriptions. For example, `text_list_1` contains the price tag's info, and `text_list_2` contains the printed text on the back of the item.

# TODO

- add "text_threshold" option.
- use Keras data generator instead of moving files around.
