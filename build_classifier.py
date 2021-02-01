import os

classdict = {
    "BEGINSPEECH": "speech",
    "CONTINUESPEECH": "speech",
    "BEGINDESCRIPTION": "note",
    "CONTINUEDESCRIPTION": "note",
    "ENDSPEECH": None,
    "ENDDESCRIPTION": None,
}

def get_files(traintest="train/", indices=[0]):
    folder = "data/curation/"
    for decennium in os.listdir(folder):
        decennium_path = folder + decennium + "/"
        if os.path.isdir(decennium_path):
            print(decennium_path)

            for index in indices:
                fpath = decennium_path + traintest + str(index) + "/annotated.txt"

                print(fpath, os.path.exists(fpath))

                yield open(fpath).read()


def get_pairs(indices):
    strings = get_files(indices=indices)
    current_class = None
    for string in strings:
        words = string.split()
        
        for word in words:
            if word in classdict:
                current_class = classdict[word]
            elif current_class is not None:
                yield (word, current_class)


import fasttext
import numpy as np
import tensorflow as tf

print("Load word vectors...")
ft = fasttext.load_model('cc.sv.300.bin')
#ft = fasttext.load_model('cc.sv.100.bin')
#ft = fasttext.load_model('cc.sv.25.bin')
dim = ft.get_word_vector("hej").shape[0]

print("Done.")

def get_set(indices=[0]):
    x = []
    y = []
    classes = dict()

    for w, c in get_pairs(indices):
        print(w, "=>", c)
        
        classes[c] = classes.get(c, 0) + 1

        if classes[c] < 1300:
            x.append(w)
            y.append(c)

    print(classes)
    class_keys = list(classes.keys())
    y = [class_keys.index(y_ix) for y_ix in y]

    for ix, x_ix in enumerate(x):
        x[ix] = ft.get_word_vector(x_ix)

    x = tf.constant(x)
    y = tf.constant(y)
    dset = tf.data.Dataset.from_tensor_slices((x, y))

    return dset, class_keys

dataset, class_keys = get_set(indices=[0,1])
dataset = dataset.shuffle(10000, reshuffle_each_iteration=False)

test_dataset = dataset.take(500) 
train_dataset = dataset.skip(500)

train_dataset = train_dataset.batch(32)
test_dataset = test_dataset.batch(32)

model = tf.keras.Sequential()
model.add(tf.keras.Input(shape=(dim,)))
model.add(tf.keras.layers.Dense(25, activation='relu'))
model.add(tf.keras.layers.Dense(len(class_keys)))

sloss = tf.keras.losses.SparseCategoricalCrossentropy(
    from_logits=True, reduction="auto", name="sparse_categorical_crossentropy"
)

model.compile(optimizer='adam', metrics=['accuracy'], loss=sloss)
model.fit(train_dataset, validation_data=test_dataset, epochs=25)

y_pred = model.predict_classes(test_dataset)

y_true = test_dataset.map(lambda x , y: y)
y_true = y_true.flat_map(lambda x: tf.data.Dataset.from_tensor_slices(x))
y_true = np.array(list(y_true.as_numpy_iterator()))

con_mat = tf.math.confusion_matrix(labels=y_true, predictions=y_pred).numpy()
con_mat_norm = np.around(con_mat.astype('float') / con_mat.sum(axis=1)[:, np.newaxis], decimals=2)
print(con_mat)

print("Confusion matrix")
print(con_mat_norm)

words = ["jag", "av", "herr", "vi", "nästa"]
V = len(words)
x = np.zeros((V, dim))

for ix, word in enumerate(words):
    vec = ft.get_word_vector(word)
    x[ix] = vec

pred = model.predict(x, batch_size=V)
biases = model.predict(np.zeros(x.shape), batch_size=V)
classes = model.predict_classes(x, batch_size=V)

print("Predictions for:", ", ".join(words))
print(pred)
print(pred - biases)
words_and_preds = zip(words, classes)

temperature = 1.0#0.3
exp_pred = tf.math.exp(pred * temperature)
exp_pred_norm = np.around(exp_pred / exp_pred.numpy().sum(axis=1)[:, np.newaxis], decimals=2)

for word, c in words_and_preds:
    print(word, c)

print(exp_pred_norm)

def classify_paragraph(s, prior = tf.math.log([0.8, 0.2])):
    words = s.split()
    V = len(words)
    x = np.zeros((V, dim))

    for ix, word in enumerate(words):
        vec = ft.get_word_vector(word)
        x[ix] = vec

    pred = model.predict(x, batch_size=V)
    biases = model.predict(np.zeros(x.shape), batch_size=V)
    #print(pred)
    return tf.reduce_sum(pred, axis=0) + prior

class_numbers = {wd: ix for ix, wd in enumerate(class_keys)}

def get_paragraphs():
    current_class = None
    classified_paragraphs = []

    unclassified = []
    for string in get_files(traintest="test/", indices=[0,1]):
        paragraphs = string.split("\n\n")
        
        for paragraph in paragraphs:
            current_paragraph = []

            words = paragraph.split()

            print("paragraph:")
            print(paragraph)
            print()

            for word in words:
                if word in classdict:
                    p = " ".join(current_paragraph)
                    if current_class is not None and len(p) > 0:
                        classified_paragraphs.append((p, current_class))
                    current_paragraph = []
                    if classdict[word] is not None:
                        current_class = class_numbers[classdict[word]]
                    else:
                        current_class = None
                else:
                    current_paragraph.append(word)
        
            last_p = " ".join(current_paragraph)
            if len(last_p) > 0 and current_class is not None:
                classified_paragraphs.append((last_p, current_class))

    return classified_paragraphs

p = "Herr talman!"

preds = classify_paragraph(p)

print(preds)

exp_pred = tf.math.exp(preds)
exp_pred_norm = exp_pred / tf.reduce_sum(exp_pred)

print(exp_pred_norm)

classified_paragraphs = get_paragraphs()

real_classes = []
pred_classes = []

for paragraph, real_class in classified_paragraphs:
    real_classes.append(real_class)
    preds = classify_paragraph(paragraph)
    print(preds)
    ix = int(np.argmax(preds))
    pred_classes.append(ix)
    print("real:", real_class, "pred:", ix, "correct:", real_class == ix)


con_mat = tf.math.confusion_matrix(labels=real_classes, predictions=pred_classes).numpy()
con_mat_norm = np.around(con_mat.astype('float') / con_mat.sum(axis=1)[:, np.newaxis], decimals=2)

print(con_mat)

print("Confusion matrix")
print(con_mat_norm)

model.save("segment-classifier/")