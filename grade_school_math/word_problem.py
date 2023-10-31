import re
import json
import nltk
from word2number import w2n

from typing import Optional, Tuple, Union, Self, List

from fractions import Fraction
import numeral

nltk.download("punkt")

INT_OR_FLT = r"\d+(?:\.\d+)?"
FRAC = rf"{INT_OR_FLT}/{INT_OR_FLT}"


class WordProblem:
    def __init__(self, question, answer):
        self.q_raw = question
        self.a_raw = answer
        self.q_numeric_quantities, self.q_quantities = self.decompose_question(
            self.q_raw
        )
        # decompose answer
        a_parts = answer.split("\n")
        self.sol = float(
            re.findall(r"\#\#\#\#\s*(\S+)\s*", a_parts[-1].replace(",", ""))[0]
        )
        self.clar, self.steps_raw = [], []
        for part in a_parts[:-1]:
            q_soc, a_soc = part.split("**")
            self.clar.append(q_soc.strip())
            self.steps_raw.append((a_soc.strip()))
        self.steps, self.calcs = [], []
        self.step_quantities, self.calc_quantities = [], []
        for step_raw in self.steps_raw:
            step = re.sub(r"<<([^<>]+=[^<>]+)>>", "", step_raw)
            self.steps.append(step)
            self.step_quantities.append(re.findall(r"\d+(?:\.\d+)?", step))
            calc = re.findall(r"<<([^<>]+=[^<>]+)>>", step_raw)
            self.calcs.append(calc)
            quantities = []
            for c in calc:
                quantities.extend(re.findall(r"\d+(?:\.\d+)?", c))
            self.calc_quantities.append(quantities)

    #         self.q_quantities = self.extract_numerals(self.q_raw)
    #         self.

    def decompose_question(self, raw):
        raw = raw.replace("-", "")
        numeric_quantities, quantities, numeral_seq = [], [], False
        for token, tag in nltk.pos_tag(nltk.tokenize.word_tokenize(raw)):
            quantity = self.extract_digitized(token.replace(",", ""))
            if quantity is not None:
                numeral_seq = False
                numeric_quantities.append(quantity)
                quantities.append(quantity)
            elif token in numeral.NUMERAL:
                if not numeral_seq:
                    numeral_seq = True
                    quantities.append([(token, tag)])
                else:
                    quantities[-1].append((token, tag))
            elif numeral_seq:
                numeral_seq = False
                number = self.parse_numeral(quantities[-1])
                if number is not None:
                    quantities[-1] = number
                else:
                    del quantities[-1]
        return numeric_quantities, quantities

    def extract_digitized(self, token) -> Optional[Union[float, Fraction]]:
        """
        Check if a digitized quantity exists within a token;
        currently detects numbers and fractions written with a slash.
        """
        frac = re.findall(rf"({FRAC})", token)
        if len(frac) not in (0, 1):
            print("warning: misshapen fraction:", frac, token)
            return None
        elif len(frac) == 1:
            elts = re.findall(INT_OR_FLT, frac[0])
            if len(elts) != 2:
                print("warning: misshapen fraction:", frac, token)
                return None
            else:
                return Fraction(numerator=int(elts[0]), denominator=int(elts[1]))
        elif len(frac) == 0:
            number = re.findall(INT_OR_FLT, token)
            if len(number) > 1:
                print("warning: misshapen number:", number, token)
                return None
            elif len(number) == 1:
                return float(number[0])

    def parse_numeral(
        self, tagged_numerals: List[Tuple[str, str]]
    ) -> List[Union[float, Fraction]]:
        numerals, tags = (e[0] for e in tagged_numerals), (
            e[1] for e in tagged_numerals
        )
        if tags[-1].startswith("NN") and numerals[-1] in numeral.INCIDENTAL:
            numerals, tags = numerals[:-1], tags[:-1]
        if len(numerals) > 1 and "JJ" in tags and tags[-1] != "JJ":
            i = tags.index("JJ") + 1
            return self.parse_numeral(
                list(zip(numerals[:i], tags[:i]))
            ) + self.parse_numeral(list(zip(numerals[i:], tags[i:])))
        if len(numerals) == 1:
            return [numeral.NUMERAL[numerals[0]]]
        else:
            if self.cardinal(numerals):
                return [float(w2n.word_to_num(" ".join(numerals)))]
            elif self.cardinal(numerals[:-1]):
                final = (
                    numerals[-1:][:-1] if numerals[-1].endswith("s") else numerals[-1]
                )
                if final in numeral.ORDINAL:
                    if tags[-1].startswith("NN"):
                        return [
                            Fraction(
                                numerator=int(w2n.word_to_num(" ".join(numerals[:-1]))),
                                denominator=numeral.ORDINAL[final],
                            )
                        ]
                    elif tags[-1] == "JJ":
                        numerals = numerals[:-1] + numeral.ORDINAL_TO_CARDINAL[final]
                        return [float(w2n.word_to_num(" ".join(numerals)))]
                    else:
                        print("warning: malformed numerals:", tagged_numerals)
                        return []

    @staticmethod
    def cardinal(tokens):
        return False not in [token in numeral.CARDINAL for token in tokens]

    @classmethod
    def from_json(cls, j) -> Self:
        return cls(question=j["question"], answer=j["answer"])

    @classmethod
    def from_file(cls, path) -> List[Self]:
        wps = []
        with open(path) as f:
            for line in f.readlines():
                if line:
                    try:
                        wps.append(WordProblem.from_json(json.loads(line)))
                    except Exception as e:
                        print("line:", line)
                        raise e
        return wps
