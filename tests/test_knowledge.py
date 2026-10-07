import unittest

from knowledge import load_knowledge, normalize_text, retrieve, search_knowledge
from utils.build_knowledge import RAW_PATH, parse_raw

SAMPLE = """\
TITRE (info)
- Premier fait
- Deuxième fait
  qui continue

AUTRE TITRE

Sous-titre
- Fait caché
"""


class ParseRawTest(unittest.TestCase):
    def test_sections_subsections_and_continuations(self):
        fragments = parse_raw(SAMPLE)
        self.assertEqual(fragments, [
            {"section": "TITRE (info)", "text": "Premier fait"},
            {"section": "TITRE (info)", "text": "Deuxième fait qui continue"},
            {"section": "AUTRE TITRE", "subsection": "Sous-titre", "text": "Fait caché"},
        ])

    def test_real_data_keeps_accented_sections(self):
        fragments = parse_raw(RAW_PATH.read_text(encoding="utf-8"))
        sections = {f["section"] for f in fragments}
        for expected in ("MANOIR (terminé)", "MYSTÈRES & QUÊTES", "LIEUX CLÉS", "RÈGLES & PHÉNOMÈNES"):
            self.assertIn(expected, sections)


class SearchTest(unittest.TestCase):
    def setUp(self):
        self.knowledge = [
            {"section": "VILLAGE", "text": "Le moulin est sûrement la solution"},
            {"section": "PERSONNAGES", "subsection": "Lavitz", "text": "Sœur de Lavitz gravement malade"},
        ]

    def test_normalize_ignores_accents_and_case(self):
        self.assertEqual(normalize_text("Sûrement ÉLÈVE"), "surement eleve")

    def test_accent_insensitive_match(self):
        self.assertEqual(len(search_knowledge("SUREMENT", self.knowledge)), 1)

    def test_all_words_must_match_in_any_order(self):
        self.assertEqual(len(search_knowledge("malade lavitz", self.knowledge)), 1)
        self.assertEqual(search_knowledge("moulin lavitz", self.knowledge), [])

    def test_matches_subsection_and_empty_query(self):
        self.assertEqual(len(search_knowledge("personnages lavitz", self.knowledge)), 1)
        self.assertEqual(search_knowledge("   ", self.knowledge), [])


class RetrieveTest(unittest.TestCase):
    def setUp(self):
        self.knowledge = [
            {"section": "VILLAGE", "text": "Le moulin est sûrement la solution"},
            {"section": "PERSONNAGES", "subsection": "Lavitz", "text": "Sœur de Lavitz gravement malade"},
            {"section": "LIEUX", "text": "Taverne : Welbone"},
        ]

    def test_natural_question_finds_relevant_fragment(self):
        result = retrieve("Qui est malade dans la famille de Lavitz ?", self.knowledge)
        self.assertEqual(result[0]["text"], "Sœur de Lavitz gravement malade")

    def test_ranks_by_shared_words_and_ignores_stopwords(self):
        result = retrieve("Que sait-on du moulin et de Lavitz malade ?", self.knowledge)
        self.assertEqual([f["section"] for f in result], ["PERSONNAGES", "VILLAGE"])

    def test_nothing_relevant_gives_empty_list(self):
        self.assertEqual(retrieve("Parle-moi des dragons", self.knowledge), [])


class LoadKnowledgeTest(unittest.TestCase):
    def test_missing_file_gives_empty_list(self):
        self.assertEqual(load_knowledge("fichier_inexistant.json"), [])


if __name__ == "__main__":
    unittest.main()
