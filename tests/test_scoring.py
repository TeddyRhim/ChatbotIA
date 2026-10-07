import unittest

from eval.scoring import (cited_fiches, facts_present, flags_uncertainty, is_abstention,
                          proper_names, score_case, ungrounded_names)

FRAGMENTS = [
    {"section": "PERSONNAGES", "subsection": "Elowen", "aliases": ["la Gardienne"],
     "text": "Faits : Gardienne de la tour de Vélan"},
    {"section": "LIEUX", "subsection": "Tour de Vélan", "aliases": [], "text": "Faits : Au nord d'Aldoria"},
]


class FactsTest(unittest.TestCase):
    def test_all_groups_needed_one_alternative_each_accents_ignored(self):
        groups = [["Elowen"], ["tour", "phare"]]
        self.assertTrue(facts_present("La gardienne Élowen vit dans une TOUR.", groups))
        self.assertFalse(facts_present("Elowen est gardienne.", groups))

    def test_sources_block_is_ignored(self):
        self.assertFalse(facts_present("Réponse vide.\n\nSources :\n[1] [PERSONNAGES > Elowen]", [["Elowen"]]))


class MarkersTest(unittest.TestCase):
    def test_abstention(self):
        self.assertTrue(is_abstention("Je ne sais pas, les extraits ne le disent pas."))
        self.assertTrue(is_abstention("Ce n'est pas mentionné dans les notes."))
        self.assertFalse(is_abstention("Le chat s'appelle Moustache."))

    def test_uncertainty(self):
        self.assertTrue(flags_uncertainty("C'est une théorie du joueur, pas un fait."))
        self.assertTrue(flags_uncertainty("Les notes se contredisent à ce sujet."))
        self.assertTrue(flags_uncertainty("Cette information doit être confirmée."))
        self.assertFalse(flags_uncertainty("Elowen est la sœur du roi."))


class GroundingTest(unittest.TestCase):
    def test_names_exclude_sentence_starts(self):
        self.assertEqual(proper_names("Selon les notes, Elowen garde la tour. Voici Korrin."), ["Elowen", "Korrin"])

    def test_invented_names_are_detected(self):
        text = "Elowen travaille avec Gandalf."
        self.assertEqual(ungrounded_names(text, "Qui est Elowen ?", FRAGMENTS), ["Gandalf"])

    def test_names_from_question_and_aliases_are_grounded(self):
        self.assertEqual(ungrounded_names("Elle sert avec Maren.", "Et Maren ?", FRAGMENTS), [])

    def test_cited_fiches(self):
        self.assertEqual(cited_fiches("Vrai [2] et [1] et [9].", FRAGMENTS), ["Tour de Vélan", "Elowen"])


class ScoreCaseTest(unittest.TestCase):
    def test_fact_case_passes_with_fact_and_source(self):
        case = {"question": "Qui garde la tour ?", "type": "fait", "facts": [["Elowen"]]}
        checks, invented = score_case(case, "Elowen la garde [1].\n\nSources :\n[1] [PERSONNAGES > Elowen]", FRAGMENTS)
        self.assertTrue(checks["passed"])
        self.assertEqual(invented, [])

    def test_fact_without_supporting_citation_fails(self):
        case = {"question": "Où est la tour ?", "type": "fait", "facts": [["nord"]]}
        # « nord » est dans la fiche 2, mais la réponse ne cite que la fiche 1
        checks, _ = score_case(case, "Au nord [1].", FRAGMENTS)
        self.assertTrue(checks["faits"])
        self.assertFalse(checks["source"])
        self.assertTrue(score_case(case, "Au nord [2].", FRAGMENTS)[0]["passed"])
        self.assertFalse(score_case(case, "Au nord, sans citation.", FRAGMENTS)[0]["passed"])

    def test_abstention_case_fails_when_model_invents(self):
        case = {"question": "Quel âge a Elowen ?", "type": "abstention"}
        checks, _ = score_case(case, "Elowen a 300 ans.", FRAGMENTS)
        self.assertFalse(checks["abstention"])
        self.assertFalse(checks["passed"])

    def test_invented_name_fails_even_with_correct_fact(self):
        case = {"question": "Qui garde la tour ?", "type": "fait", "facts": [["Elowen"]]}
        checks, invented = score_case(case, "Elowen et son ami Gandalf la gardent.", FRAGMENTS)
        self.assertTrue(checks["faits"])
        self.assertFalse(checks["ancrage"])
        self.assertEqual(invented, ["Gandalf"])

    def test_uncertain_case(self):
        case = {"question": "Elowen est-elle la sœur du roi ?", "type": "incertain"}
        self.assertTrue(score_case(case, "C'est une hypothèse, pas confirmée.", FRAGMENTS)[0]["passed"])


if __name__ == "__main__":
    unittest.main()
