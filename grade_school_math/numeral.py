"""
(non-frozen) constants describing categories of English numerals
"""

import copy
from fractions import Fraction

CARDINAL = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
    "thousand": 1000,
    "million": 1000000,
    "billion": 1000000000,
    "trillion": 1000000000000,
}

MISC = {
    "nil": 0,
    "nothing": 0,
    "zilch": 0,
    "nada": 0,
    "zip": 0,
    "solo": 1,
    "couple": 2,
    "pair": 2,
    "duo": 2,
    "penultimate": 2,
    "trio": 3,
    "antipenultimate": 3,
    "quartet": 4,
    "preantepenultimate": 4,
    "quintet": 5,
    "sextet": 6,
    "septet": 7,
    "octet": 8,
    "nonet": 9,
    "decade": 10,
    "dozen": 12,
    "baker 's dozen": 13,
    "baker's dozen": 13,
    "bakers dozen": 13,
    "baker dozen": 13,
    "century": 100,
    "millennium": 1000,
}

MULTIPLICATIVE = {
    "once": 1,
    "twice": 2,
    "thrice": 3,
    "solitary": 1,
    "singular": 1,
    "double": 2,
    "twofold": 2,
    "duplicate": 2,
    "triple": 3,
    "threefold": 3,
    "triplicate": 3,
    "quadruple": 4,
    "fourfold": 4,
    "quintuple": 5,
    "fivefold": 5,
    "sextuple": 6,
    "hextuple": 6,
    "sixfold": 6,
    "septuple": 7,
    "heptuple": 7,
    "sevenfold": 7,
}

ORDINAL_TO_CARDINAL = {
    "zeroth": "zero",
    "first": "one",
    "second": "two",
    "third": "three",
    "fourth": "four",
    "fifth": "five",
    "sixth": "six",
    "seventh": "seven",
    "eighth": "eight",
    "ninth": "nine",
    "tenth": "ten",
    "eleventh": "eleven",
    "twelfth": "twelve",
    "thirteenth": "thirteen",
    "fourtheenth": "fourteen",
    "fifteenth": "fifteen",
    "sixteenth": "sixteen",
    "seventeenth": "seventeen",
    "eighteenth": "eighteen",
    "ninteenth": "nineteen",
    "twentieth": "twenty",
    "thirtieth": "thirty",
    "fortieth": "forty",
    "fiftieth": "fifty",
    "sixtieth": "sixty",
    "seventieth": "seventy",
    "eightieth": "eighty",
    "ninetieth": "ninety",
    "hundredth": "hundred",
    "thousandth": "thousand",
    "millionth": "million",
    "billionth": "billion",
    "trillionth": "trillion",
}

ORDINAL = {
    key: CARDINAL[ORDINAL_TO_CARDINAL[key]] for key in ORDINAL_TO_CARDINAL.keys()
}

PARTITIVE = {
    "whole": 1,
    "half": Fraction(1, 2),
    "quarter": Fraction(1, 4),
}

INCIDENTAL = {"second"}

NUMERAL = copy.deepcopy(CARDINAL)
NUMERAL.update(MISC)
NUMERAL.update(MULTIPLICATIVE)
NUMERAL.update(ORDINAL)
NUMERAL.update(PARTITIVE)
