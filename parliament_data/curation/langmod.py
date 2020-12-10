import re


def loss(sentence):
    return 0.0

def improvement(sentence, regexp):
    sentence_suggestion = regexp
    loss0 = loss(sentence)
    loss1 = loss(sentence_suggestion)

    return loss0, loss1