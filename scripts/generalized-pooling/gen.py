'''
Generate 
'''
import argparse
import theano
import numpy
import cPickle as pkl
import os
from data_iterator import TextIterator

from main import (build_model, pred_probs, prepare_data, pred_acc, load_params,
                 init_params, init_tparams)

def main():
    model_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
    model = '../../models/{}.npz'.format(model_name)
    dev_datasets =['../../data/word_sequence/premise_snli_1.0_dev.txt', 
                   '../../data/word_sequence/hypothesis_snli_1.0_dev.txt',
                   '../../data/word_sequence/label_snli_1.0_dev.txt']
    test_datasets=['../../data/word_sequence/premise_snli_1.0_test.txt', 
                   '../../data/word_sequence/hypothesis_snli_1.0_test.txt',
                   '../../data/word_sequence/label_snli_1.0_test.txt']
    dictionary   = '../../data/word_sequence/vocab_cased.pkl'

    # load model model_options
    with open('%s.pkl' % model, 'rb') as f:
        options = pkl.load(f)

    print options
    # load dictionary and invert
    with open(dictionary, 'rb') as f:
        word_dict = pkl.load(f)
    word_idict = dict()
    for kk, vv in word_dict.iteritems():
        word_idict[vv] = kk

    dev = TextIterator(dev_datasets[0], dev_datasets[1], dev_datasets[2], 
                       dictionary,
                       n_words=options['n_words'],
                       batch_size=options['valid_batch_size'],
                       shuffle=False)

    test = TextIterator(test_datasets[0], test_datasets[1], test_datasets[2], 
                        dictionary,
                        n_words=options['n_words'],
                        batch_size=options['valid_batch_size'],
                        shuffle=False)

    # allocate model parameters
    params = init_params(options, word_dict)

    # load model parameters and set theano shared variables
    params = load_params(model, params)
    tparams = init_tparams(params)

    trng, use_noise, \
        x1, x1_mask, char_x1, char_x1_mask, x2, x2_mask, char_x2, char_x2_mask, y, \
        opt_ret, \
        cost, \
        f_pred, f_prods = \
        build_model(tparams, options)

    use_noise.set_value(0.)
    dev_acc = pred_acc(f_pred, prepare_data, options, dev, word_idict)
    test_acc = pred_acc(f_pred, prepare_data, options, test, word_idict)

    print 'dev accuracy', dev_acc
    print 'test accuracy', test_acc

    predict_labels_dev = pred_label(f_prods, prepare_data, options, dev, word_idict)
    predict_labels_test = pred_label(f_prods, prepare_data, options, test, word_idict)

    with open('predict_gold_samples_dev.txt', 'w') as fw:
        with open(dev_datasets[0], 'r') as f1:
            with open(dev_datasets[1], 'r') as f2:
                with open(dev_datasets[-1], 'r') as f3:
                    for a, b, c, d in zip(predict_labels_dev, f3, f1, f2):
                        fw.write(str(a) + '\t' + b.rstrip() + '\t' + c.rstrip() + '\t' + d.rstrip() + '\n')

    with open('predict_gold_samples_test.txt', 'w') as fw:
        with open(test_datasets[0], 'r') as f1:
            with open(test_datasets[1], 'r') as f2:
                with open(test_datasets[-1], 'r') as f3:
                    for a, b, c, d in zip(predict_labels_test, f3, f1, f2):
                        fw.write(str(a) + '\t' + b.rstrip() + '\t' + c.rstrip() + '\t' + d.rstrip() + '\n')

    print 'Done'

def pred_label(f_prods, prepare_data, options, iterator, word_idict):
    labels = []
    valid_acc = 0
    n_done = 0
    for x1_, x2_, y_ in iterator:
        n_done += len(x1_)
        lengths_x1 = [len(s) for s in x1_]
        lengths_x2 = [len(s) for s in x2_]
        x1, x1_mask, char_x1, char_x1_mask, x2, x2_mask, char_x2, char_x2_mask, y = prepare_data(x1_, x2_, y_, word_idict)
        inps = [x1, x1_mask, char_x1, char_x1_mask, x2, x2_mask, char_x2, char_x2_mask]
        prods = f_prods(*inps)
        preds = prods.argmax(axis=1)
        valid_acc += (preds == y).sum()
        labels = labels + preds.tolist()

    valid_acc = 1.0 * valid_acc / n_done
    print "total sampel", n_done
    print "Acc", valid_acc

    return labels

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main()
