import unittest

from knowledge import load_knowledge, normalize_text, retrieve, search_knowledge
from utils.build_knowledge import SAMPLE_LORE, build, parse_fiches

SAMPLE = """# Elowen
alias: la Gardienne, Elo
statut: alliée
- Premier fait
- Deuxième fait
  qui continue
- (hypothèse) Une idée

# Tour
- Un lieu
"""


class ParseFichesTest(unittest.TestCase):
    def test_fiche_fields_and_rendering(self):
        fiches = parse_fiches(SAMPLE, "PERSONNAGES")
        self.assertEqual(len(fiches), 2)
        elowen = fiches[0]
        self.assertEqual(elowen["section"], "PERSONNAGES")
        self.assertEqual(elowen["subsection"], "Elowen")
        self.assertEqual(elowen["aliases"], ["la Gardienne", "Elo"])
        self.assertEqual(
            elowen["text"],
            "Alias : la Gardienne, Elo. Statut : alliée. "
            "Faits : Premier fait ; Deuxième fait qui continue ; (hypothèse) Une idée",
        )

    def test_fiche_without_metadata(self):
        self.assertEqual(parse_fiches(SAMPLE, "LIEUX")[1]["text"], "Faits : Un lieu")

    def test_sample_lore_builds_and_underscore_files_are_ignored(self):
        fragments = build(SAMPLE_LORE)
        self.assertGreater(len(fragments), 5)
        self.assertIn("Cristal d'aube", {f["subsection"] for f in fragments})
        self.assertTrue(all(f["text"] and f["section"] for f in fragments))


class SearchTest(unittest.TestCase):
    def setUp(self):
        self.knowledge = [
            {"section": "PORT", "text": "Le phare est sûrement la solution"},
            {"section": "PERSONNAGES", "subsection": "Elowen", "text": "Sœur d'Elowen gravement malade"},
        ]

    def test_normalize_ignores_accents_and_case(self):
        self.assertEqual(normalize_text("Sûrement ÉLÈVE"), "surement eleve")

    def test_accent_insensitive_match(self):
        self.assertEqual(len(search_knowledge("SUREMENT", self.knowledge)), 1)

    def test_all_words_must_match_in_any_order(self):
        self.assertEqual(len(search_knowledge("malade elowen", self.knowledge)), 1)
        self.assertEqual(search_knowledge("phare elowen", self.knowledge), [])

    def test_matches_subsection_and_empty_query(self):
        self.assertEqual(len(search_knowledge("personnages elowen", self.knowledge)), 1)
        self.assertEqual(search_knowledge("   ", self.knowledge), [])


class RetrieveTest(unittest.TestCase):
    def setUp(self):
        self.knowledge = [
            {"section": "PORT", "text": "Le phare est sûrement la solution"},
            {"section": "PERSONNAGES", "subsection": "Elowen", "text": "Sœur d'Elowen gravement malade"},
            {"section": "LIEUX", "text": "Taverne : Welbone"},
        ]

    def test_natural_question_finds_relevant_fragment(self):
        result = retrieve("Qui est malade dans la famille de Elowen ?", self.knowledge)
        self.assertEqual(result[0]["text"], "Sœur d'Elowen gravement malade")

    def test_ranks_by_shared_words_and_ignores_stopwords(self):
        result = retrieve("Que sait-on du phare et de Elowen malade ?", self.knowledge)
        self.assertEqual([f["section"] for f in result], ["PERSONNAGES", "PORT"])

    def test_alias_and_name_outweigh_plain_mentions(self):
        knowledge = [
            {"section": "LIEUX", "subsection": "Tour", "aliases": [],
             "text": "Gardée par Korrin, ennemi de Korrin"},
            {"section": "PERSONNAGES", "subsection": "Korrin", "aliases": ["Korin"], "text": "Un chevalier"},
        ]
        self.assertEqual(retrieve("Qui est Korin ?", knowledge)[0]["subsection"], "Korrin")

    def test_nothing_relevant_gives_empty_list(self):
        self.assertEqual(retrieve("Parle-moi des dragons", self.knowledge), [])


class LoadKnowledgeTest(unittest.TestCase):
    def test_missing_file_gives_empty_list(self):
        self.assertEqual(load_knowledge("fichier_inexistant.json"), [])


if __name__ == "__main__":
    unittest.main()
