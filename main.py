import os.path
import tensorflow as tf
import helper
import warnings
from distutils.version import LooseVersion
import project_tests as tests
import glob


# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    warnings.warn('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))


def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    assert tf.saved_model.loader.maybe_saved_model_directory(vgg_path), 'wrong path to vgg16'

    vgg_tag = 'vgg16'
    vgg_input_tensor_name = 'image_input:0'
    vgg_keep_prob_tensor_name = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'
    tf.saved_model.loader.load(sess, [vgg_tag], vgg_path)
    image_input = sess.graph.get_tensor_by_name(vgg_input_tensor_name)
    keep_prob = sess.graph.get_tensor_by_name(vgg_keep_prob_tensor_name)
    layer3_out = sess.graph.get_tensor_by_name(vgg_layer3_out_tensor_name)
    layer4_out = sess.graph.get_tensor_by_name(vgg_layer4_out_tensor_name)
    layer7_out = sess.graph.get_tensor_by_name(vgg_layer7_out_tensor_name)

    return image_input, keep_prob, layer3_out, layer4_out, layer7_out

tests.test_load_vgg(load_vgg, tf)


def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer7_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer3_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # TODO: Implement function
    # print(vgg_layer3_out.get_shape().as_list())
    # 1x1 Convolution
    layer_1_1_num_out = vgg_layer7_out.get_shape().as_list()[3]
    layer_1_1 = tf.layers.conv2d(vgg_layer7_out, 
                                    layer_1_1_num_out, 
                                    kernel_size=(1,1), 
                                    strides=(1,1), 
                                    activation=tf.nn.relu,
                                    name='layer_1_1')

    deconv_layer_1_num_out = vgg_layer4_out.get_shape().as_list()[3] #num_classes
    deconv_layer_1 = tf.layers.conv2d_transpose(layer_1_1, 
                                                deconv_layer_1_num_out, 
                                                kernel_size=(4,4), 
                                                strides=(2, 2), 
                                                padding='same',
                                                activation=tf.nn.relu,
                                                name='deconv_layer_1')

    skip_1 = tf.add(deconv_layer_1, vgg_layer4_out, name='skip_1')

    deconv_layer_2_num_out = vgg_layer3_out.get_shape().as_list()[3]
    deconv_layer_2 = tf.layers.conv2d_transpose(skip_1, 
                                                deconv_layer_2_num_out, 
                                                kernel_size=(4,4), 
                                                strides=(2, 2),
                                                padding='same',
                                                activation=tf.nn.relu,
                                                name='deconv_layer_2')

    skip_2 = tf.add(deconv_layer_2, vgg_layer3_out, name='skip_2')

    deconv_layer_3_num_out = num_classes
    deconv_layer_3 = tf.layers.conv2d_transpose(skip_2, 
                                                deconv_layer_3_num_out, 
                                                kernel_size=(16,16), 
                                                strides=(8, 8), 
                                                padding='same',
                                                activation=tf.nn.relu,
                                                name='deconv_layer_3')

    return deconv_layer_3

tests.test_layers(layers)


def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    # TODO: Implement function

    logits = tf.reshape(nn_last_layer, (-1, num_classes))
    labels = tf.reshape(correct_label, (-1, num_classes))

    cross_entropy_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=labels))

    train_op = tf.train.GradientDescentOptimizer(learning_rate).minimize(cross_entropy_loss)

    return logits, train_op, cross_entropy_loss

tests.test_optimize(optimize)


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
    # TODO: Implement function
    rate = 0.001
    dropout = 0.5
    display_step = 1

    step = 0
     
    for images, labels in get_batches_fn(batch_size):

        print(images.shape)

        sess.run(train_op, feed_dict={input_image: images, 
                                        correct_label: labels,
                                        keep_prob: dropout,
                                        learning_rate: rate})

        
        if step % display_step == 0:
            loss = sess.run(cross_entropy_loss, feed_dict={input_image: images, 
                                                        correct_label: labels, 
                                                        keep_prob: 1.0})
            print("Iter: " + str(step) + " Loss: {:.6f}".format(loss))
        step += 1
        
        pass

tests.test_train_nn(train_nn)


def run():
    num_classes = 2
    image_shape = (160, 576)
    data_dir = './data'
    runs_dir = './runs'
   
    epochs = 20
    batch_size = 5


    tests.test_for_kitti_dataset(data_dir)
    tf.logging.set_verbosity(tf.logging.DEBUG)
    # Download pretrained vgg model
    helper.maybe_download_pretrained_vgg(data_dir)

    # input_image = tf.placeholder(tf.float32, [None, image_shape[0], image_shape[1], num_classes])
    correct_label = tf.placeholder(tf.float32, [None, image_shape[0], image_shape[1], num_classes])
    learning_rate = tf.placeholder(tf.float32)
    keep_prob = tf.placeholder(tf.float32)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/

    with tf.Session() as sess:
        
        # Path to vgg model
        vgg_path = os.path.join(data_dir, 'vgg')
        # Create function to get batches
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)
        num_images = len(glob.glob(os.path.join(data_dir, 'data_road/training/calib/*.*')))
        # batch_per_epoch = int(num_images/batch_size) + 1
        print("Num images: " + str(num_images) + " Batch size: " + str(batch_size))
        

        # OPTIONAL: Augment Images for better results
        #  https://datascience.stackexchange.com/questions/5224/how-to-prepare-augment-images-for-neural-network

        # TODO: Build NN using load_vgg, layers, and optimize function
        image_input, keep_prob, layer3_out, layer4_out, layer7_out = load_vgg(sess, vgg_path)
        output = layers(layer3_out, layer4_out, layer7_out, num_classes)
        logits, train_op, cross_entropy_loss = optimize(output, correct_label, learning_rate, num_classes)
        # writer = tf.summary.FileWriter("output", sess.graph)
        # TODO: Train NN using the train_nn function
        sess.run([tf.global_variables_initializer(), tf.local_variables_initializer()])
        train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, image_input,
             correct_label, keep_prob, learning_rate)


        # TODO: Save inference data using helper.save_inference_samples
        #  helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, keep_prob, input_image)

        # OPTIONAL: Apply the trained model to a video
        # writer.close()

if __name__ == '__main__':
    run()
