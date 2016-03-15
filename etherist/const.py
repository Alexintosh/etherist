
import os

THRESHOLD_PRICE_ABOVE = 'price_above'
THRESHOLD_PRICE_BELOW = 'price_below'
THRESHOLDS = {}
THRESHOLDS[THRESHOLD_PRICE_ABOVE] = ['When price reaches above', 'Price reached above']
THRESHOLDS[THRESHOLD_PRICE_BELOW] = ['When price reaches below', 'Price reached below']
DATA_DIR = os.path.dirname(os.path.realpath(__file__)) + '/../data'
