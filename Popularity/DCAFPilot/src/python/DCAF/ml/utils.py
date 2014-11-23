#!/usr/bin/env python
#-*- coding: utf-8 -*-
#pylint: disable=
"""
File       : utils.py
Author     : Valentin Kuznetsov <vkuznet AT gmail dot com>
Description: generic module with useful set of utilites
"""

# system modules
import optparse
from math import log, exp

# B. Bounded logloss
# INPUT:
#     p: our prediction
#     y: real answer
# OUTPUT
#     bounded logarithmic loss of p given y
def logloss(p, y):
    """
    Provide logloss function for prediction/real values arrays. Here p is 
    an array of prediciton and y is an array of real values
    """
    p = max(min(p, 1. - 10e-16), 10e-16)
    return -log(p) if y == 1. else -log(1. - p)

class GLF(object):
    def __init__(self, a=0, k=1, b=1, q=1, m=0, nu=1):
        "GLF (Generalized Logistic Function) object"
        self.a = a
        self.k = k
        self.b = b
        self.q = q
        self.m = m
        self.nu = nu
    def __repr__(self):
        "Representation of GLF object"
        return "<GenLogFunc(a=%s, k=%s, b=%s, q=%s, m=%s, nu=%s)>, http://www.wikiwand.com/en/Generalised_logistic_function" \
                % (self.a, self.k, self.b, self.q, self.m, self.nu)
    def logistic(self, t):
        "Generalized logistic function"
        return self.a+(self.k-self.a)/(1.+self.q*exp(-self.b*(t-self.m)))**(1/self.nu)
    def sigmoid(self, t):
        "Generalized logistic function reduced to sigmoid function"
        return 1./(1.+exp(-t))
    def tanh(self, t):
        "hyperbolic tangent function"
        return (1.+tanh(t))/2. # bounded tanh (in [0,1] range)
    def algebraic(self, t):
        "algebraic function"
        return t/sqrt(1.+t**2)
    def absval(self, t):
        "absolute value function"
        return t/(1.+abs(t))
    def guderman(self, t):
        "Gudermannian function"
        return (2./pi)*atan(pi*t/2.)

def best_features(clf, xdf, targets):
    "Find, print and return best features using simple classifier"
    fit = clf.fit(xdf, targets)
    features = xdf.columns
    importances = clf.feature_importances_
    sorted_idx = np.argsort(importances)
    best_features = features[sorted_idx][::-1]
    best_indecies = importances[sorted_idx][::-1]
    print "Best features/importances:"
    for key, val in zip(best_features, best_indecies):
        print "   %20s: %.3f" % (key, val)
    return best_features

def keep_features(xdf, features):
    "Return dataset with desired features"
    drops = [c for c in xdf.columns if c not in features]
    return xdf.drop(drops, axis=1)

def norm_data(col, xdf, tdf):
    "Normalize given column in input/output datasets"
    # example by using StandardScaler
    # df['var'] = StandardScaler().fit_transform(df.var)
    # but here we need to combine both datasets into one and scale them across
    # all values, so we'll do it manually
    minval = min(xdf[col].min(), tdf[col].min())
    maxval = max(xdf[col].max(), tdf[col].max())
    meanval = (xdf[col].mean() + tdf[col].mean())/2.
    xnorm = (xdf[col] - meanval)/(maxval - minval)
    ynorm = (xdf[col] - meanval)/(maxval - minval)
    return xnorm, ynorm

def normalize(columns, xdf, tdf):
    "Normalize input/output datasets"
    for col in columns:
        if  col in xdf.columns and col in tdf.columns:
            xdf[col], tdf[col] = norm_data(col, xdf, tdf)

class OptionParser(object):
    "Option parser"
    def __init__(self, learners=None, scorers=None):
        self.parser = optparse.OptionParser()
        if  learners:
            learners.sort()
        if  scorers:
            scorers.sort()
        scalers = ['StandardScaler', 'MinMaxScaler']
        self.parser.add_option("--scaler", action="store", type="string",
            default="", dest="scaler",
            help="model scalers: %s, default None" % scalers)
        self.parser.add_option("--scorer", action="store", type="string",
            default="", dest="scorer",
            help="model scorers: %s, default None" % scorers)
        self.parser.add_option("--learner", action="store", type="string",
            default="RandomForestClassifier", dest="learner",
            help="model learners: %s" % learners)
        self.parser.add_option("--learner-params", action="store", type="string",
            default="", dest="lparams",
            help="model classifier parameters, supply via JSON")
        self.parser.add_option("--train-file", action="store", type="string",
            default="train.csv", dest="train", help="train file, default train.csv")
        self.parser.add_option("--test-file", action="store", type="string",
            default="", dest="test", help="test file, default no test file")
        self.parser.add_option("--idx", action="store", type="int",
            default=0, dest="idx",
            help="initial index counter, default 0")
        self.parser.add_option("--limit", action="store", type="int",
            default=10000, dest="limit",
            help="number of rows to process, default 10000")
        self.parser.add_option("--verbose", action="store", type="int",
            default=0, dest="verbose",
            help="verbose output, default=0")
        self.parser.add_option("--roc", action="store_true",
            default=False, dest="roc",
            help="plot roc curve")
        self.parser.add_option("--full", action="store_true",
            default=False, dest="full",
            help="Use full sample for training, i.e. don't split")
        self.parser.add_option("--crossval", action="store_true",
            default=False, dest="cv",
            help="Perform cross-validation for given model and quit")
        self.parser.add_option("--gsearch", action="store", type="string",
            default=None, dest="gsearch",
            help="perform grid search, gsearch=<parameters>")
        self.parser.add_option("--predict", action="store_true",
            default=False, dest="predict",
            help="Yield prediction, used by pylearn")
    def options(self):
        "Returns parse list of options"
        return self.parser.parse_args()

