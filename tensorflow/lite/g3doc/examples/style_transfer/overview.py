import streamlit as st
import tensorflow as tf
import PIL
print(
  tf.__version__)

import IPython.display as display

import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['figure.figsize'] = (12,12)
mpl.rcParams['axes.grid'] = False

import numpy as np
import time
import functools

# Function to load an image from a file, and add a batch dimension.
def load_img(path_to_img):
  img = tf.io.read_file(path_to_img)
  img = tf.io.decode_image(img, channels=3)
  img = tf.image.convert_image_dtype(img, tf.float32)
  img = img[tf.newaxis, :]

  return img

# Function to pre-process by resizing an central cropping it.
def preprocess_image(image, target_dim):
  # Resize the image so that the shorter dimension becomes 256px.
  shape = tf.cast(tf.shape(image)[1:-1], tf.float32)
  short_dim = min(shape)
  scale = target_dim / short_dim
  new_shape = tf.cast(shape * scale, tf.int32)
  image = tf.image.resize(image, new_shape)

  # Central crop the image.
  image = tf.image.resize_with_crop_or_pad(image, target_dim, target_dim)

  return image

def imshow(image, title=None):
  if len(image.shape) > 3:
    image = tf.squeeze(image, axis=0)

  plt.imshow(image)
  if title:
    plt.title(title)

# Function to run style prediction on preprocessed style image.
def run_style_predict(preprocessed_style_image):
  # Load the model.
  interpreter = tf.lite.Interpreter(model_path=style_predict_path)

  # Set model input.
  interpreter.allocate_tensors()
  input_details = interpreter.get_input_details()
  interpreter.set_tensor(input_details[0]["index"], preprocessed_style_image)

  # Calculate style bottleneck.
  interpreter.invoke()
  style_bottleneck = interpreter.tensor(
      interpreter.get_output_details()[0]["index"]
      )()

  return style_bottleneck

# Run style transform on preprocessed style image
def run_style_transform(style_bottleneck, preprocessed_content_image):
  # Load the model.
  interpreter = tf.lite.Interpreter(model_path=style_transform_path)

  # Set model input.
  input_details = interpreter.get_input_details()
  interpreter.allocate_tensors()

  # Set model inputs.
  interpreter.set_tensor(input_details[0]["index"], preprocessed_content_image)
  interpreter.set_tensor(input_details[1]["index"], style_bottleneck)
  interpreter.invoke()

  # Transform content image.
  stylized_image = interpreter.tensor(
      interpreter.get_output_details()[0]["index"]
      )()

  return stylized_image

st.write('# Image stylization')
with st.form("my_form"):
  st.write("Inside the form")
  image_to_style=st.text_input("Image to style")
  chosen_style=st.text_input("Chosen style")

   # Every form must have a submit button.
  submitted = st.form_submit_button("Submit")
  if submitted:
    st.write("image", image_to_style, "style", chosen_style)

    content_path = tf.keras.utils.get_file('user_image_input.jpg',image_to_style)
    style_path = tf.keras.utils.get_file('user_style_input.jpg',chosen_style)

    style_predict_path = tf.keras.utils.get_file('style_predict.tflite', 'https://tfhub.dev/google/lite-model/magenta/arbitrary-image-stylization-v1-256/int8/prediction/1?lite-format=tflite')
    style_transform_path = tf.keras.utils.get_file('style_transform.tflite', 'https://tfhub.dev/google/lite-model/magenta/arbitrary-image-stylization-v1-256/int8/transfer/1?lite-format=tflite')



    # Load the input images.
    content_image = load_img(content_path)
    style_image = load_img(style_path)

    # Preprocess the input images.
    preprocessed_content_image = preprocess_image(content_image, 384)
    preprocessed_style_image = preprocess_image(style_image, 256)

    print('Style Image Shape:', preprocessed_style_image.shape)
    print('Content Image Shape:', preprocessed_content_image.shape)




    plt.subplot(1, 2, 1)
    imshow(preprocessed_content_image, 'Content Image')

    plt.subplot(1, 2, 2)
    imshow(preprocessed_style_image, 'Style Image')



    # Calculate style bottleneck for the preprocessed style image.
    style_bottleneck = run_style_predict(preprocessed_style_image)
    print('Style Bottleneck Shape:', style_bottleneck.shape)



    # Stylize the content image using the style bottleneck.
    stylized_image = run_style_transform(style_bottleneck, preprocessed_content_image)

    st.image(stylized_image)

    # Visualize the output.
    #imshow(stylized_image, 'Stylized Image')
    #cv2.imwrite('leac1bg.png', stylized_image) 

    # Visualize the output.


    imshow(stylized_image, 'Stylized Image')



    # Calculate style bottleneck of the content image.
    style_bottleneck_content = run_style_predict(
        preprocess_image(content_image, 256)
        )


    # Define content blending ratio between [0..1].
    # 0.0: 0% style extracts from content image.
    # 1.0: 100% style extracted from content image.
    content_blending_ratio = 0.5 #@param {type:"slider", min:0, max:1, step:0.01}

    # Blend the style bottleneck of style image and content image
    style_bottleneck_blended = content_blending_ratio * style_bottleneck_content \
                              + (1 - content_blending_ratio) * style_bottleneck

    # Stylize the content image using the style bottleneck.
    stylized_image_blended = run_style_transform(style_bottleneck_blended,
                                                preprocessed_content_image)

    # Visualize the output.
    imshow(stylized_image_blended, 'Blended Stylized Image')

