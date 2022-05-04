import os
import random
import numpy as np
from PIL import Image
import tensorflow as tf
import alex_hyperparameters as hp

class Datasets():
    def __init__(self, data_path):

        self.data_path = data_path
        self.idx_to_class = {}
        self.class_to_idx = {}
        self.classes = [""] * hp.num_classes
        self.mean = np.zeros((3,))
        self.std = np.zeros((3,))
        self.calc_mean_and_std()

        self.train_data = self.get_data(os.path.join(self.data_path, "train"), True, True)
        self.test_data = self.get_data(os.path.join(self.data_path, "test"), False, False)

    def calc_mean_and_std(self):
        file_list = []
        for root, _, files in os.walk(os.path.join(self.data_path, "train")):
            for name in files:
                if name.endswith(".jpg"):
                    file_list.append(os.path.join(root, name))
        random.shuffle(file_list)
        file_list = file_list[:hp.preprocess_sample_size]
        data_sample = np.zeros((hp.preprocess_sample_size, hp.img_size, hp.img_size, 3))

        # Import images
        for i, file_path in enumerate(file_list):
            img = Image.open(file_path)
            img = img.resize((hp.img_size, hp.img_size))
            img = np.array(img, dtype=np.float32)
            img /= 255.

            if len(img.shape) == 2:
                img = np.stack([img, img, img], axis=-1)

            data_sample[i] = img

        self.mean = np.mean(data_sample, axis=(0, 1, 2))
        self.std = np.std(data_sample, axis=(0, 1, 2))

        print("Dataset mean: [{0:.4f}, {1:.4f}, {2:.4f}]".format(self.mean[0], self.mean[1], self.mean[2]))
        print("Dataset std: [{0:.4f}, {1:.4f}, {2:.4f}]".format(self.std[0], self.std[1], self.std[2]))

    def standardize(self, img):
        img -= self.mean
        img /= self.std
        return img

    def preprocess_fn(self, img):
        img = img / 255.
        img = self.standardize(img)
        return img


    def get_data(self, path, shuffle, augment):

        if augment:
            data_gen = tf.keras.preprocessing.image.ImageDataGenerator(preprocessing_function=self.preprocess_fn,
                zoom_range=0.5,
                shear_range=10.,
                horizontal_flip=True,
                rotation_range=20)
        else:
            data_gen = tf.keras.preprocessing.image.ImageDataGenerator(preprocessing_function=self.preprocess_fn)

        img_size = 224
        classes_for_flow = None

        # Make sure all data generators are aligned in label indices
        if bool(self.idx_to_class):
            classes_for_flow = self.classes

        # Form image data generator from directory structure
        data_gen = data_gen.flow_from_directory(
            path,
            target_size=(img_size, img_size),
            class_mode='sparse',
            batch_size=hp.batch_size,
            shuffle=shuffle,
            classes=classes_for_flow)

        # Setup the dictionaries if not already done
        if not bool(self.idx_to_class):
            unordered_classes = []
            for dir_name in os.listdir(path):
                if os.path.isdir(os.path.join(path, dir_name)):
                    unordered_classes.append(dir_name)

            for img_class in unordered_classes:
                self.idx_to_class[data_gen.class_indices[img_class]] = img_class
                self.class_to_idx[img_class] = int(data_gen.class_indices[img_class])
                self.classes[int(data_gen.class_indices[img_class])] = img_class

        return data_gen
