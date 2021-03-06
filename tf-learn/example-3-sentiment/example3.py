# example-3-simple-sentiment.py
import numpy as np
np.random.seed(42)
import tensorflow as tf
tf.set_random_seed(42)
from datetime import datetime
import time
# import cPickle as pickle
import pickle

# reset everything to rerun in jupyter
tf.reset_default_graph()

# config
batch_size = 100
learning_rate = 0.5
training_epochs = 6
logs_path = './tmp/example-3/' + datetime.now().isoformat()

N_Class = 2
N_X = 423 # len(train_x[0])
layer1_size = 32

train_x, train_y, test_x, test_y = pickle.load( open('tmp/sentiment_set.pickle', 'rb' ) )
train_x = train_x.toarray() # as we stored the data as sparse matrix, restore them back to numpy array
test_x = test_x.toarray()

# input images
with tf.name_scope('input'):
    # None -> batch size can be any size
    x = tf.placeholder(tf.float32, shape=[None, N_X], name="x-input") 
    # target 10 output classes
    y_ = tf.placeholder(tf.float32, shape=[None, N_Class], name="y-input")

# model parameters will change during training so we use tf.Variable
with tf.name_scope("weights"):
    W1 = tf.Variable(tf.truncated_normal([N_X, layer1_size], stddev=0.1)) # version 2 change
    W = tf.Variable(tf.truncated_normal([layer1_size, N_Class], stddev=1.0))

# bias
with tf.name_scope("biases"):
    b1 = tf.Variable(tf.zeros([layer1_size]))
    b = tf.Variable(tf.zeros([N_Class]))

with tf.name_scope('hidden_layers'):
    y1 = tf.nn.relu(tf.matmul(x, W1) + b1)

# implement model
with tf.name_scope("softmax"):
    # y is our prediction
    ylogits = tf.matmul(y1, W) + b
    y = tf.nn.softmax(ylogits)

# specify cost function
with tf.name_scope('cross_entropy'):
    # this is our cost
    cross_entropy = tf.nn.softmax_cross_entropy_with_logits(logits=ylogits, labels=y_)
    cross_entropy = tf.reduce_mean(cross_entropy)

# specify optimizer
with tf.name_scope('train'):
    # optimizer is an "operation" which we can execute in a session
    train_op = tf.train.AdamOptimizer(learning_rate=0.001).minimize(cross_entropy)
    # version 2 change, previous using GradientDescentOptimizer(learning_rate)

with tf.name_scope('accuracy'):
    # Accuracy
    correct_prediction = tf.equal(tf.argmax(y,1), tf.argmax(y_,1))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
    
# create a summary for our cost and accuracy
train_cost_summary = tf.summary.scalar("train_cost", cross_entropy)
train_acc_summary = tf.summary.scalar("train_accuracy", accuracy)
test_cost_summary = tf.summary.scalar("test_cost", cross_entropy)
test_acc_summary = tf.summary.scalar("test_accuracy", accuracy)

# merge all summaries into a single "operation" which we can execute in a session 
# summary_op = tf.summary.merge_all()

with tf.Session() as sess:
    # variables need to be initialized before we can use them
    sess.run(tf.global_variables_initializer())

    # create log writer object
    writer = tf.summary.FileWriter(logs_path, graph=tf.get_default_graph())
        
    # perform training cycles
    for epoch in range(training_epochs):
        # number of batches in one epoch
        batch_count = int(len(train_x)/batch_size)
        i = 0
        for _b in range(batch_count):
            start = i
            end = i + batch_size
            batch_x = np.array(train_x[start:end])
            batch_y = np.array(train_y[start:end])
            
            # perform the operations we defined earlier on batch
            _, train_cost, train_acc, _train_cost_summary, _train_acc_summary = \
                sess.run([train_op, cross_entropy, accuracy, train_cost_summary, train_acc_summary], 
                    feed_dict={x: batch_x, y_: batch_y})
            # write log
            writer.add_summary(_train_cost_summary, epoch * batch_count + _b)
            writer.add_summary(_train_acc_summary, epoch * batch_count + _b)

            if i % 100 == 0:
                # for log on test data:
                test_cost, test_acc, _test_cost_summary, _test_acc_summary = \
                    sess.run([cross_entropy, accuracy, test_cost_summary, test_acc_summary], 
                        feed_dict={x: test_x, y_: test_y})
                # write log
                writer.add_summary(_test_cost_summary, epoch * batch_count + _b)
                writer.add_summary(_test_acc_summary, epoch * batch_count + _b)
                
                print('Epoch {0:3d}, Batch {1:3d} | Train Cost: {2:.2f} | Test Cost: {3:.2f} | Accuracy batch train: {4:.2f} | Accuracy test: {5:.2f}'
                    .format(epoch, i, train_cost, test_cost, train_acc, test_acc))
            i += batch_size
    print('Accuracy: {}'.format(accuracy.eval(feed_dict={x: test_x , y_: test_y})))
    print('done')

# tensorboard --logdir=./tmp/example-3 --port=8002 --reload_interval=5
# You can run the following js code in broswer console to make tensooboard to do auto-refresh
# setInterval(function() {document.getElementById('reload-button').click()}, 5000);
