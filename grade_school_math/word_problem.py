import re
import json
import nltk
from word2number import w2n
import pprint

from typing import Tuple, Self, List

import numeral

nltk.download("punkt")

INT_OR_FLT = r"\d+(?:\.\d*)?"
RATIO = rf"{INT_OR_FLT}/{INT_OR_FLT}|{INT_OR_FLT}:{INT_OR_FLT}"
SOLUTION_QUANT = r"\#\#\#\#\s*(\S+)\s*"
CALCULATION = r"<<[^<>]+=[^<>]+>>"
CALCULATION_EXPR = r"<<([^<>]+=[^<>]+)>>"
HYPHENATION = r"([a-zA-Z])-([a-zA-Z])"


class WordProblem:
    def __init__(self, question, answer):
        self.q_raw, self.a_raw = self.tidy(question), self.tidy(answer)
        self.q_numeric_quantities, self.q_quantities = self.decompose_question(
            self.q_raw
        )
        (
            self.solution,
            self.socratic_questions,
            self.calculation_annotated_steps,
            self.text_steps,
            self.calculation_steps,
            self.text_step_quantities,
            self.calculation_step_quantities_lhs,
            self.calculation_step_quantities_rhs,
        ) = self.decompose_answer(self.a_raw)
        (
            self.q_multiplicities,
            self.text_step_multiplicities,
            self.unspecified_or_underived_quantities,
            self.unusued_quantities,
        ) = self.detect_missing_calculations(
            self.q_quantities,
            self.text_step_quantities,
            self.calculation_step_quantities_lhs,
            self.calculation_step_quantities_rhs,
        )
        # (self.program,) = self.assemble_program(
        #     self.missing_calculations,
        #     self.q_quantities,
        #     self.text_step_quantities,
        #     self.calculation_step_quantities,
        #     self.calculation_steps,
        #     self.solution,
        # )

    def tidy(self, s):
        return s.replace("\u2013", "-")

    def decompose_question(self, raw):
        raw = self.preprocess(raw)
        numeric_quantities, quantities, numeral_seq = [], [], False
        for token, tag in nltk.pos_tag(nltk.tokenize.word_tokenize(raw)):
            if token in numeral.NUMERAL:
                if not numeral_seq:
                    numeral_seq = True
                    quantities.append([(token, tag)])
                else:
                    quantities[-1].append((token, tag))
            else:
                if numeral_seq:
                    numeral_seq = False
                    numbers = self.parse_numeral(quantities[-1])
                    del quantities[-1]
                    if numbers:
                        quantities.extend(numbers)
                numbers = self.extract_digitized(token.replace(",", ""))
                if numbers is not None:
                    numeric_quantities.extend(numbers)
                    quantities.extend(numbers)
            
        return numeric_quantities, quantities

    def preprocess(self, s):
        return re.sub(HYPHENATION, lambda m: " ".join(m.group(1, 2)), s)

    def extract_digitized(self, token) -> List[float]:
        ratio = re.findall(rf"({RATIO})", token)
        if len(ratio) not in (0, 1):
            raise ValueError(f"misshapen ratio: {ratio}, {token}")
        elif len(ratio) == 1:
            elts = re.findall(INT_OR_FLT, ratio[0])
            if len(elts) != 2:
                raise ValueError(f"misshapen ratio: {ratio}, {token}")
            else:
                return [float(elts[0]), float(elts[1])]
        elif len(ratio) == 0:
            number = re.findall(rf"({INT_OR_FLT})[^0-9]?.*", token)
            if len(number) > 1:
                raise ValueError(f"misshapen number: {number}, {token}")
            elif len(number) == 1:
                return [float(number[0])]
            
        return None

    def parse_numeral(self, tagged_numerals: List[Tuple[str, str]]) -> List[float]:
        if len(tagged_numerals) == 0:
            return []
        numerals, tags = [e[0] for e in tagged_numerals], [
            e[1] for e in tagged_numerals
        ]
        if tags[-1].startswith("NN") and numerals[-1] in numeral.INCIDENTAL:
            numerals, tags = numerals[:-1], tags[:-1]
            if len(numerals) == 0:
                return []
        if len(numerals) > 1 and "JJ" in tags and tags[-1] != "JJ":
            i = tags.index("JJ") + 1
            return self.parse_numeral(
                list(zip(numerals[:i], tags[:i]))
            ) + self.parse_numeral(list(zip(numerals[i:], tags[i:])))
        if len(numerals) == 1:
            return [float(numeral.NUMERAL[numerals[0]])]
        else:
            if self.cardinal(numerals):
                return [float(self.safe_word_to_num(" ".join(numerals)))]
            elif self.cardinal(numerals[:-1]):
                final = (
                    numerals[-1:][:-1] if numerals[-1].endswith("s") else numerals[-1]
                )
                if final in numeral.ORDINAL:
                    if not tags[-1].startswith("JJ"):
                        return [
                            float(self.safe_word_to_num(" ".join(numerals[:-1]))),
                            float(numeral.ORDINAL[final]),
                        ]
                    else:
                        numerals = numerals[:-1] + [numeral.ORDINAL_TO_CARDINAL[final]]
                        return [float(self.safe_word_to_num(" ".join(numerals)))]

    @staticmethod
    def cardinal(tokens):
        return False not in [token in numeral.CARDINAL for token in tokens]

    @classmethod
    def safe_word_to_num(cls, s):
        try:
            return w2n.word_to_num(s)
        except Exception as e:
            print(f"w2n.word_to_num failed on: {s}")
            raise e

    def decompose_answer(
        self, raw: str
    ) -> Tuple[
        float,
        List[str],
        List[str],
        List[str],
        List[str],
        List[List[float]],
        List[List[float]],
    ]:
        lines = self.preprocess(raw).split("\n")
        solution_quantities = re.findall(SOLUTION_QUANT, lines[-1].replace(",", ""))
        if len(solution_quantities) != 1:
            raise ValueError(
                f"multiple quantities found in solution line: {solution_quantities}: {raw}"
            )
        solution, exchanges = float(solution_quantities[0]), lines[:-1]
        socratic_questions, calculation_annotated_steps = [], []
        for exchange in exchanges:
            q, a = exchange.split("**")
            socratic_questions.append(q.strip())
            calculation_annotated_steps.append((a.strip()))
        text_steps, calculation_steps = [], []
        text_step_quantities, calculation_step_quantities_lhs, calculation_step_quantities_rhs = [], [], []
        for calculation_annotated_step in calculation_annotated_steps:
            text_step = re.sub(CALCULATION, "", calculation_annotated_step)
            text_steps.append(text_step)
            text_step_quantities.append(
                [float(t) for t in re.findall(INT_OR_FLT, text_step)]
            )
            calculation_step = re.findall(CALCULATION_EXPR, calculation_annotated_step)
            calculation_steps.append(calculation_step)
            quantities_lhs, quantities_rhs = [], []
            for c in calculation_step:
                lhs, rhs = c.split("=")
                quantities_lhs.append([float(t) for t in re.findall(INT_OR_FLT, lhs)])
                quantities_rhs.append([float(t) for t in re.findall(INT_OR_FLT, rhs)])
            calculation_step_quantities_lhs.append(quantities_lhs)
            calculation_step_quantities_rhs.append(quantities_rhs)
        return (
            solution,
            socratic_questions,
            calculation_annotated_steps,
            text_steps,
            calculation_steps,
            text_step_quantities,
            calculation_step_quantities_lhs,
            calculation_step_quantities_rhs,
        )

    def detect_missing_calculations(
        self, q_quantities, text_step_quantities, calculation_step_quantities_lhs, calculation_step_quantities_rhs
    ):
        try:
            q_multiplicities = {}
            for v in q_quantities:
                if v in q_multiplicities:
                    q_multiplicities[v] += 1
                else:
                    q_multiplicities[v] = 1
            text_step_multiplicities = {}
            for vs in text_step_quantities:
                for v in vs:
                    if v in text_step_multiplicities:
                        text_step_multiplicities[v] += 1
                    else:
                        text_step_multiplicities[v] = 1
            calculation_lhs_values = set()
            for vss in calculation_step_quantities_lhs:
                for vs in vss:
                    for v in vs:
                        calculation_lhs_values.add(v)
            calculation_rhs_values = set()
            for vss in calculation_step_quantities_rhs:
                for vs in vss:
                    for v in vs:
                        calculation_rhs_values.add(v)
            q_values = set(q_multiplicities.keys())
            text_step_values = set(text_step_multiplicities.keys())
            specified = q_values.intersection(text_step_values)
            unspecified_or_underived_or_derived = \
                text_step_values - q_values
            derived = unspecified_or_underived_or_derived.intersection(
                calculation_rhs_values)
            unspecified_or_underived = \
                unspecified_or_underived_or_derived - derived
            unused = specified - calculation_lhs_values
            return (
                q_multiplicities,
                text_step_multiplicities,
                unspecified_or_underived,
                unused,
            )
        except Exception as e:
            print(self)
            raise e

    def assemble_program(
        self,
        q_quantities,
        text_step_quantities,
        calculation_step_quantities,
        calculation_steps,
        solution,
    ):
        pass

    @classmethod
    def from_json(cls, j) -> Self:
        return cls(question=j["question"], answer=j["answer"])

    @classmethod
    def from_file(cls, path, encoding="utf-8") -> List[Self]:
        wps = []
        with open(path, encoding=encoding) as f:
            for line in f.readlines():
                if line:
                    try:
                        wps.append(WordProblem.from_json(json.loads(line)))
                    except Exception as e:
                        print("line:", line)
                        raise e
        return wps

    def __str__(self):
        return pprint.pformat(
            (
                ("q_raw", self.q_raw),
                ("a_raw", self.a_raw),
                ("q_numeric_quantities", self.q_numeric_quantities),
                ("q_quantities", self.q_quantities),
                ("solution", self.solution),
                ("socratic_questions", self.socratic_questions),
                ("calculation_annotated_steps", self.calculation_annotated_steps),
                ("text_steps", self.text_steps),
                ("calculation_steps", self.calculation_steps),
                ("text_step_quantities", self.text_step_quantities),
                ("calculation_step_quantities_lhs", self.calculation_step_quantities_lhs),
                ("calculation_step_quantities_rhs", self.calculation_step_quantities_rhs),
                ("q_multiplicities", self.q_multiplicities), 
                ("text_step_multiplicities", self.text_step_multiplicities),
                ("unspecified_or_underived_quantities", self.unspecified_or_underived_quantities),
                ("unused_quantities", self.unusued_quantities),
            ),
            indent=4,
        )
