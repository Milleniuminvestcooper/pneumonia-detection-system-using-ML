# -*- coding: utf-8 -*-
"""Citi-Scan_Pneumonia.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1SVi3m3nBTZau2VzZsRz2Mypr_2gr8w19

![An image](https://cdn.the-scientist.com/assets/articleNo/67625/aImg/38176/ct-thumb.png)

>Pneumonia, a prevalent respiratory threat globally and particularly in regions like Tanzania, presents a critical need for fast and accurate diagnosis to ensure effective treatment. However, existing diagnostic processes encounter challenges, leading to delays and potential inaccuracies in pneumonia detection. The manual interpretation of medical imaging, such as X-rays, MRI, and CT scans, is resource-intensive and susceptible to human error.

## Group Members
| S/N  |STUDENT NAME   |REGISTRATION NUMBER|POGRAM   |   |
|---|---|---|---|---|
|  1 |  SAIDI ALLY ATHUMANI		 | T21-03-03113  |  BSC-HIS |   |
|  2 |DAVID DAUSON RUTALOMBA   | T21-03-12925  | BSC-HIS  |   |
|  3 | BARAKA GODFREY GISHA  | T21-03-05608  | BSC-HIS  |   |
|4|PATRICK RICHARD|T21-03-13227|BSC-HIS| |
|5|NEEMA JOSHUA|T21-03-10273|BSC-HIS||
"""

# Commented out IPython magic to ensure Python compatibility.
# Tensorflow and Keras Libraries
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import tensorflow as tf
import keras
from tensorflow import keras
from keras import backend as K
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Flatten
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import SparseCategoricalCrossentropy
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import LearningRateScheduler

# Data Libraries
import pandas as pd
import numpy as np

# Image libraries
import cv2
from PIL import Image
import scipy.ndimage as nd

# Graphing libraries
import matplotlib.pyplot as plt
import seaborn as sns
from mlxtend.plotting import plot_confusion_matrix
# %matplotlib inline

# Utils Libraries
import os
import random
import warnings
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report
warnings.filterwarnings(action="ignore")
annealer = LearningRateScheduler(lambda x: 1e-3 * 0.95 ** x, verbose=0)

"""####*Global variables*"""

EPOCHS = 10
LR=0.001
RANDOM_STATE = 42
model_path = './CitiScan-pneumonia.h5'

def get_files():
  data_dir = './drive/MyDrive/pneumonia_CT'
  train_dir = os.path.join(data_dir, 'Train')
  val_dir = os.path.join(data_dir, 'Val')
  test_dir = os.path.join(data_dir, 'Test')

  return train_dir, val_dir, test_dir, data_dir

def display_CT_images():
  files = []
  cats = []
  train_dir, val_dir, test_dir, data_dir = get_files()
  filenames = os.listdir(os.path.join(train_dir, 'NORMAL'))
  for file in filenames:
    files.append(os.path.join(train_dir, 'NORMAL', file))
    cats.append('NORMAL')

  filenames = os.listdir(os.path.join(train_dir, 'PNEUMONIA'))
  for file in filenames:
    files.append(os.path.join(train_dir, 'PNEUMONIA', file))
    cats.append('PNEUMONIA')

  img_count = 12
  file_idx = random.sample(range(len(files)), img_count)
  rand_fig = plt.figure(figsize=(12, 8))
  for idx in range(img_count):
    rand_fig.add_subplot(3, 4, idx + 1)
    plt.imshow(cv2.imread(files[file_idx[idx]]))
    plt.title(cats[file_idx[idx]])
    plt.axis('off')
  plt.show()

"""display_CT_images()"""

def get_data_dirs():
  train_dir, val_dir, test_dir, _ = get_files()
  normal_paths = [
    f'{train_dir}/NORMAL',
    f'{val_dir}/NORMAL',
    f'{test_dir}/NORMAL'
  ]
  pneumonia_paths = [
      f'{train_dir}/PNEUMONIA',
      f'{val_dir}/PNEUMONIA',
      f'{test_dir}/PNEUMONIA'
  ]
  data_dirs = [normal_paths, pneumonia_paths]
  filepaths = []
  labels = []
  classes = ['Normal', 'Pneumonia']
  #
  for idx, paths in enumerate(data_dirs):
    for path in paths:
      file_lst = os.listdir(path)
      for f in file_lst:
        fpath = os.path.join(path, f)
        filepaths.append(fpath)
        labels.append(classes[idx])

  file_series = pd.Series(filepaths, name='filepaths')
  lable_series = pd.Series(labels, name='labels')
  data = pd.concat([file_series, lable_series], axis =1 )
  df = pd.DataFrame(data)

  return data, df

def plot_CT_classes():
  _, df = get_data_dirs()
  plt.figure(figsize = (10, 4))
  sns.histplot(data=df, x='labels', hue='labels')
  plt.title('Patients per condition');

"""plot_CT_classes()

### Data Preparation

##### 1. Split the dataset
"""

def split_datasets():
  _, df = get_data_dirs()
  train_imgs, test_imgs = train_test_split(df, test_size = 0.3, random_state = RANDOM_STATE)
  train_set, val_set = train_test_split(df, test_size = 0.2, random_state = RANDOM_STATE)

  return train_imgs, test_imgs, train_set, val_set

"""#### ii. Prepare dataset"""

def imageDataGenerator():
  return ImageDataGenerator(preprocessing_function=tf.keras.applications.mobilenet_v2.preprocess_input)

def image_formatter():
  image_gen = imageDataGenerator()
  train_imgs, test_imgs, train_set, val_set = split_datasets()
  train = image_gen.flow_from_dataframe(dataframe= train_set,x_col="filepaths",y_col="labels",
                                      target_size=(244,244),
                                      color_mode='rgb',
                                      class_mode="categorical",
                                      batch_size=4,
                                      shuffle=False
                                     )
  test = image_gen.flow_from_dataframe(dataframe= test_imgs,x_col="filepaths", y_col="labels",
                                     target_size=(244,244),
                                     color_mode='rgb',
                                     class_mode="categorical",
                                     batch_size=4,
                                     shuffle= False
                                    )
  val = image_gen.flow_from_dataframe(dataframe= val_set,x_col="filepaths", y_col="labels",
                                    target_size=(244,244),
                                    color_mode= 'rgb',
                                    class_mode="categorical",
                                    batch_size=4,
                                    shuffle=False
                                   )

  return train, test, val

"""### Create CT-Scan Model"""

def create_CT_model():
  train, test, val = image_formatter()
  model = keras.models.Sequential([
          keras.layers.Conv2D(filters=128, kernel_size=(8, 8), strides=(3, 3), activation='relu', input_shape=(224, 224, 3)),
          keras.layers.BatchNormalization(),

          keras.layers.Conv2D(filters=256, kernel_size=(5, 5), strides=(1, 1), activation='relu', padding="same"),
          keras.layers.BatchNormalization(),
          keras.layers.MaxPool2D(pool_size=(3, 3)),

          keras.layers.Conv2D(filters=256, kernel_size=(3, 3), strides=(1, 1), activation='relu', padding="same"),
          keras.layers.BatchNormalization(),
          keras.layers.Conv2D(filters=256, kernel_size=(1, 1), strides=(1, 1), activation='relu', padding="same"),
          keras.layers.BatchNormalization(),
          keras.layers.Conv2D(filters=256, kernel_size=(1, 1), strides=(1, 1), activation='relu', padding="same"),
          keras.layers.BatchNormalization(),

          keras.layers.Conv2D(filters=512, kernel_size=(3, 3), activation='relu', padding="same"),
          keras.layers.BatchNormalization(),
          keras.layers.MaxPool2D(pool_size=(2, 2)),

          keras.layers.Conv2D(filters=512, kernel_size=(3, 3), activation='relu', padding="same"),
          keras.layers.BatchNormalization(),

          keras.layers.Conv2D(filters=512, kernel_size=(3, 3), activation='relu', padding="same"),
          keras.layers.BatchNormalization(),

          keras.layers.MaxPool2D(pool_size=(2, 2)),

          keras.layers.Conv2D(filters=512, kernel_size=(3, 3), activation='relu', padding="same"),
          keras.layers.BatchNormalization(),

          keras.layers.MaxPool2D(pool_size=(2, 2)),

          keras.layers.Flatten(),
          keras.layers.Dense(1024, activation='relu'),
          keras.layers.Dropout(0.5),
          keras.layers.Dense(1024, activation='relu'),
          keras.layers.Dropout(0.5),
          keras.layers.Dense(2, activation='softmax')
      ])
  return model

model = create_CT_model()
model.compile(loss='categorical_crossentropy', optimizer=tf.optimizers.SGD(learning_rate=LR),
              metrics=['accuracy'])
model.summary()

"""#### Model Architecture"""

from keras.utils import plot_model
plot_model(model, to_file='model_plot.png', show_shapes=True, show_layer_names=True)

train, test, val = image_formatter()

history = model.fit(train, epochs=EPOCHS, validation_data=val)

"""### Visualizing the performance of the model

##### i. Model accuracy and Model loss
"""

fig, ax = plt.subplots(1, 2, figsize = (14, 5))
ax[0].plot(history.history['accuracy'], label='Accuracy')
ax[0].plot(history.history['val_accuracy'], label='Validation accuracy')
ax[0].set_xlabel('Epochs')
ax[0].set_ylabel('Accuracy')
ax[0].set_title('Model Accuracy')
ax[0].legend()

ax[1].plot(history.history['loss'], label='Loss')
ax[1].plot(history.history['val_loss'], label='Validation loss')
ax[1].set_xlabel('Epochs')
ax[1].set_ylabel('Loss')
ax[1].legend()

plt.show()

"""##### ii. Save the trained model"""

model.save(model_path)

"""#### Evaluating the saved model"""

citi_saved_model = keras.models.load_model(model_path)

result = citi_saved_model.predict_generator(test, steps=len(test), verbose=1)

res_idx = result.argmax()
print(f'Model loss: {result[res_idx][0]:.2f}')
print(f'Model accuracy: {result[res_idx][1] * 100:.2f}%')

"""##### iii. Plotting the Confusion Matrix"""

y_preds = result.argmax(axis = -1)
y_true = test.classes

classes = train.class_indices.keys()
CM = confusion_matrix(y_true, y_preds)
fig, ax = plot_confusion_matrix(conf_mat=CM ,  figsize=(10,8), hide_ticks=True,cmap=plt.cm.Blues)
plt.xticks(range(len(classes)), classes, fontsize=12)
plt.yticks(range(len(classes)), classes, fontsize=12)
plt.title("Confusion Matrix for Model File [Test Dataset]:", fontsize=12)
plt.show()

"""#### iv. Model classification report"""

print('Models classification report:')
print(classification_report(y_true, y_preds))

"""##### v. Testing Model performance using sample images"""

image_gen = imageDataGenerator()
_, test_imgs, _, _ = split_datasets()
test_gen = image_gen.flow_from_dataframe(dataframe= test_imgs,x_col="filepaths", y_col="labels",
                                     target_size=(224,224),
                                     color_mode='rgb',
                                     class_mode="categorical",
                                     batch_size=4,
                                     shuffle= False
                                    )
numofbatch = len(test_gen)

batch_no = random.randint(0, numofbatch-1)

y_img_batch, y_true_batch = test_gen[batch_no]
y_true_batch = y_true_batch.argmax(axis=-1)

y_pred_batch = citi_saved_model.predict(y_img_batch)
y_pred_batch = y_pred_batch.argmax(axis=-1)


sizeofbatch = len(y_true_batch)
print("-"*35)
print("%s%d"%     ("Selected Batch No       : ", batch_no))
print("-"*35)
print("%s%d"%     ("Batch Size              : ", len(y_pred_batch)))
print("-"*35)
print("%s%.2f%s"% ("Accuracy                : ", np.mean(y_true==y_preds)*100, "%"))

y_pred = []
for i in range(len(y_pred_batch)):
  if y_pred_batch[i] <= 0.5:
    y_pred.append(0)
  else:
    y_pred.append(1)

LABELS_DICT = {0 : 'NORMAL', 1 : 'PNEUMONIA'}

img, label = test_gen[batch_no]
fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(10, 7))
for i, ax in enumerate(axs.flatten()):
    plt.sca(ax)
    img_scaled = np.clip(img[i], 0, 255)
    plt.imshow(img_scaled)
    plt.title('True: {}\n Pred: {}'.format(LABELS_DICT[label.argmax(axis = 1)[i]], LABELS_DICT[y_pred[i]]))
plt.suptitle('Testing model performance', fontsize=15)
plt.tight_layout()
plt.show()

