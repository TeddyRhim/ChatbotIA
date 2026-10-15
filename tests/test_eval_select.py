import unittest

from eval.eval_answers import failed_questions, select_cases

CASES = [
    {"question": "Qui est Elowen ?", "type": "fait"},
    {"question": "Où est la tour de Vélan ?", "type": "fait"},
    {"question": "Qui garde la tour ?", "type": "abstention"},
]


def row(question, passed):
    return {"question": question, "checks": {"passed": passed}}


class SelectCasesTest(unittest.TestCase):
    def test_no_filter_keeps_everything(self):
        self.assertEqual(select_cases(CASES), CASES)

    def test_only_matches_fragments_without_case(self):
        kept = select_cases(CASES, only="elowen, VÉLAN")
        self.assertEqual([c["question"] for c in kept], ["Qui est Elowen ?", "Où est la tour de Vélan ?"])

    def test_failed_keeps_listed_questions(self):
        kept = select_cases(CASES, failed={"Qui garde la tour ?"})
        self.assertEqual([c["question"] for c in kept], ["Qui garde la tour ?"])

    def test_empty_failed_set_keeps_nothing(self):
        self.assertEqual(select_cases(CASES, failed=set()), [])


class FailedQuestionsTest(unittest.TestCase):
    RESULTS = {
        "hybride": [row("Qui est Elowen ?", False), row("Qui garde la tour ?", True)],
        "hybride+liens": [row("Qui garde la tour ?", False)],
    }

    def test_uses_requested_configs(self):
        self.assertEqual(failed_questions(self.RESULTS, ["hybride"]), {"Qui est Elowen ?"})

    def test_union_over_several_configs(self):
        self.assertEqual(failed_questions(self.RESULTS, ["hybride", "hybride+liens"]),
                         {"Qui est Elowen ?", "Qui garde la tour ?"})

    def test_falls_back_to_last_config(self):
        self.assertEqual(failed_questions(self.RESULTS, ["mots-clés"]), {"Qui garde la tour ?"})


if __name__ == "__main__":
    unittest.main()
