from keras.layers import Input, Dense, Reshape, Flatten, Dropout
from keras.layers import BatchNormalization, Activation, ZeroPadding2D
from keras.layers.advanced_activations import LeakyReLU
from keras.layers.convolutional import UpSampling2D, Conv2D
from keras.models import Sequential, Model
from keras.optimizers import Adam
from keras.utils import np_utils
from tensorflow import keras
import tensorflow as tf
#from tensorflow import keras
#from keras.backend import tensorflow_backend


import matplotlib.pyplot as plt
import os
import argparse
import cv2
import numpy as np
from pathlib import Path

np.random.seed(0)
np.random.RandomState(0)
tf.compat.v1.random.set_random_seed

config = tf.compat.v1.ConfigProto(gpu_options=tf.compat.v1.GPUOptions(allow_growth=True))
session = tf.compat.v1.Session(config=config)
tf.compat.v1.keras.backend.set_session(session)

# root_dir = str(Path('idols').resolve())

class DCGAN():
    def __init__(self, root_dir):

        self.class_names = os.listdir(root_dir)

        self.shape = (128, 128, 3)
        self.z_dim = 100

        optimizer = Adam(lr=0.0002, beta_1=0.5)

        self.discriminator = self.build_discriminator()
        self.discriminator.compile(loss='binary_crossentropy', optimizer=optimizer, metrics=['accuracy'])

        self.generator = self.build_generator()
        # self.generator.compile(loss='binary_crossentropy', optimizer=optimizer)

        z = Input(shape=(self.z_dim,))
        img = self.generator(z)

        self.discriminator.trainable = False

        valid = self.discriminator(img)

        self.combined = Model(z, valid)
        self.combined.compile(loss='binary_crossentropy', optimizer=optimizer)

    def build_generator(self):
        noise_shape = (self.z_dim,)

        model = Sequential()

        model.add(Dense(128 * 32 * 32, activation="relu", input_shape=noise_shape))
        model.add(Reshape((32, 32, 128)))
        model.add(BatchNormalization(momentum=0.8))
        model.add(UpSampling2D())
        model.add(Conv2D(128, kernel_size=3, padding="same"))
        model.add(Activation("relu"))
        model.add(BatchNormalization(momentum=0.8))
        model.add(UpSampling2D())
        model.add(Conv2D(64, kernel_size=3, padding="same"))
        model.add(Activation("relu"))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Conv2D(3, kernel_size=3, padding="same"))
        model.add(Activation("tanh"))

        model.summary()

        noise = Input(shape=noise_shape)
        img = model(noise)

        return Model(noise, img)

    def build_discriminator(self):
        img_shape = self.shape

        model = Sequential()

        model.add(Conv2D(32, kernel_size=3, strides=2, input_shape=img_shape, padding="same"))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dropout(0.25))
        model.add(Conv2D(64, kernel_size=3, strides=2, padding="same"))
        model.add(ZeroPadding2D(padding=((0, 1), (0, 1))))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dropout(0.25))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Conv2D(128, kernel_size=3, strides=2, padding="same"))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dropout(0.25))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Conv2D(256, kernel_size=3, strides=1, padding="same"))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dropout(0.25))

        model.add(Flatten())
        model.add(Dense(1, activation='sigmoid'))

        model.summary()

        img = Input(shape=img_shape)
        validity = model(img)

        return Model(img, validity)

    def build_combined(self):
        self.discriminator.trainable = False
        model = Sequential([self.generator, self.discriminator])

        return model

    def train(self, root_dir, write_path, iterations, save_interval, batch_size=128, model_interval=1000, check_noise=None, r=5, c=5):

        X_train, labels = self.load_imgs(root_dir)

        half_batch = int(batch_size / 2)

        X_train = (X_train.astype(np.float32) - 127.5) / 127.5

        for iteration in range(iterations+1):

            # ------------------
            # Training Discriminator
            # -----------------
            idx = np.random.randint(0, X_train.shape[0], half_batch)

            imgs = X_train[idx]

            noise = np.random.uniform(-1, 1, (half_batch, self.z_dim))

            gen_imgs = self.generator.predict(noise)

            d_loss_real = self.discriminator.train_on_batch(imgs, np.ones((half_batch, 1)))
            d_loss_fake = self.discriminator.train_on_batch(gen_imgs, np.zeros((half_batch, 1)))

            d_loss = 0.5 * np.add(d_loss_real, d_loss_fake)

            # -----------------
            # Training Generator
            # -----------------

            noise = np.random.uniform(-1, 1, (batch_size, self.z_dim))

            g_loss = self.combined.train_on_batch(noise, np.ones((batch_size, 1)))

            print("%d [D loss: %f, acc.: %.2f%%] [G loss: %f]" % (iteration, d_loss[0], 100 * d_loss[1], g_loss))
            
            write_dir = Path(write_path)
            write_dir.mkdir(exist_ok=True)
            
            write_dir = Path(write_path + "/latent")
            write_dir.mkdir(exist_ok=True)
            
            model_dir = Path(write_path + '/ganmodels')
            model_dir.mkdir(exist_ok=True)
            
            if iteration % save_interval == 0:
                self.save_imgs(write_path, iteration, check_noise, r, c)
                start = np.expand_dims(check_noise[0], axis=0)
                end = np.expand_dims(check_noise[1], axis=0)
                resultImage = self.visualizeInterpolation(start=start, end=end)
                cv2.imwrite(write_path + "/latent/" + "latent_{1}.png".format(write_path, iteration), resultImage)
                if iteration % model_interval == 0:
                    self.generator.save(str(model_dir)+"/dcgan-{}-iter.h5".format(iteration))

    def save_imgs(self, write_path, iteration, check_noise, r, c):
        write_dir = Path(write_path + "/gen_imgs")
        write_dir.mkdir(exist_ok=True)
        noise = check_noise
        gen_imgs = self.generator.predict(noise)

        # 0-1 rescale
        gen_imgs = 0.5 * gen_imgs + 0.5

        fig, axs = plt.subplots(r, c)
        cnt = 0
        for i in range(r):
            for j in range(c):
                axs[i, j].imshow(gen_imgs[cnt, :, :, :])
                axs[i, j].axis('off')
                cnt += 1
        fig.savefig('{}/gen_imgs/img_%d.png'.format(write_path) % iteration)

        plt.close()

    def load_imgs(self, root_dir):

        img_paths = []
        labels = []
        images = []
        for cl_name in self.class_names:
            img_names = os.listdir(os.path.join(root_dir, cl_name))
            for img_name in img_names:
                img_paths.append(os.path.abspath(os.path.join(root_dir, cl_name, img_name)))
                hot_cl_name = self.get_class_one_hot(cl_name)
                labels.append(hot_cl_name)

        for img_path in img_paths:
            img = cv2.imread(img_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            images.append(img)

        images = np.array(images)

        return (np.array(images), np.array(labels))

    def get_class_one_hot(self, class_str):
        label_encoded = self.class_names.index(class_str)

        label_hot = np_utils.to_categorical(label_encoded, len(self.class_names))
        label_hot = label_hot

        return label_hot

    def visualizeInterpolation(self, start, end, save=True, nbSteps=10):
        print("Generating interpolations...")

        steps = nbSteps
        latentStart = start
        latentEnd = end

        startImg = self.generator.predict(latentStart)
        endImg = self.generator.predict(latentEnd)

        vectors = []

        alphaValues = np.linspace(0, 1, steps)
        for alpha in alphaValues:
            vector = latentStart * (1 - alpha) + latentEnd * alpha
            vectors.append(vector)

        vectors = np.array(vectors)

        resultLatent = None
        resultImage = None

        for i, vec in enumerate(vectors):
            gen_img = np.squeeze(self.generator.predict(vec), axis=0)
            gen_img = (0.5 * gen_img + 0.5) * 255
            interpolatedImage = cv2.cvtColor(gen_img, cv2.COLOR_RGB2BGR)
            interpolatedImage = interpolatedImage.astype(np.uint8)
            resultImage = interpolatedImage if resultImage is None else np.hstack([resultImage, interpolatedImage])

        return resultImage


if __name__ == '__main__':
    # コマンドライン引数を取得
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--path',  default='./idols')
    parser.add_argument('-w','--write',  default='./images')
    parser.add_argument('-i','--iters',  default=10000)
    parser.add_argument('-s','--saveitr',  default=1000)
    args = parser.parse_args()
    # 画像に日付を埋め込み
    root_dir = str(args.path)
    write_path = str(args.write)
    iterations = int(args.iters)
    save_interval = int(args.saveitr)
    
    
    dcgan = DCGAN(root_dir)
    r, c = 5, 5
    check_noise = np.random.uniform(-1, 1, (r * c, 100))
    dcgan.train(root_dir, write_path, iterations, save_interval, batch_size=32, 
                model_interval=1000, check_noise=check_noise, r=r,c=c)