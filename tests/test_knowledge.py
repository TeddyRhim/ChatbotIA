import unittest

from knowledge import ensure_citations, load_knowledge, normalize_text, retrieve, search_knowledge
from retrieval import HybridRetriever, fuse_rankings
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


class HybridTest(unittest.TestCase):
    def test_fusion_favors_items_ranked_well_in_both_lists(self):
        self.assertEqual(fuse_rankings([[1, 2, 3], [2, 9, 1]], k=2), [2, 1])

    def test_retriever_without_vector_store_uses_keywords(self):
        knowledge = [
            {"section": "PERSONNAGES", "subsection": "Elowen", "aliases": [], "text": "Gardienne de la tour"},
            {"section": "LIEUX", "subsection": "Phare", "aliases": [], "text": "Un phare au bord de la mer"},
        ]
        result = HybridRetriever(knowledge).retrieve("Qui est Elowen ?", k=1)
        self.assertEqual(result[0]["subsection"], "Elowen")


class EnsureCitationsTest(unittest.TestCase):
    FRAGMENTS = [
        {"section": "PERSONNAGES", "subsection": "Kasimir", "aliases": [],
         "text": "Faits : Elfe du crépuscule, frère de Katrina ; ancien chef des elfes, sert maintenant Strahd"},
        {"section": "LIEUX", "subsection": "Phare", "aliases": [],
         "text": "Faits : Un phare blanc au bord de la falaise nord"},
    ]

    def test_uncited_sentence_gets_the_supporting_fiche(self):
        text = "Kasimir est un elfe du crépuscule, frère de Katrina."
        self.assertEqual(ensure_citations(text, self.FRAGMENTS), text + " [1]")

    def test_each_sentence_is_matched_separately(self):
        text = "Kasimir est un elfe du crépuscule et frère de Katrina. Un phare blanc borde la falaise nord."
        out = ensure_citations(text, self.FRAGMENTS)
        self.assertIn("Katrina. [1]", out)
        self.assertTrue(out.endswith("nord. [2]"))

    def test_existing_citation_short_or_unsupported_sentences_are_untouched(self):
        for text in ("Il est elfe du crépuscule [2].",          # déjà cité (même à tort)
                     "Oui.",                                      # trop court
                     "Les extraits ne mentionnent pas le chat de Silvaréth."):  # aucune fiche ne le dit
            self.assertEqual(ensure_citations(text, self.FRAGMENTS), text)

    def test_citation_placed_after_the_full_stop_is_not_duplicated(self):
        text = "Kasimir est un elfe du crépuscule et frère de Katrina. [1] Un phare blanc borde la falaise nord. [2]"
        self.assertEqual(ensure_citations(text, self.FRAGMENTS), text)
        self.assertEqual(ensure_citations("Kasimir est un elfe du crépuscule et frère de Katrina. [1][2]", self.FRAGMENTS),
                         "Kasimir est un elfe du crépuscule et frère de Katrina. [1][2]")

    def test_no_fragments_changes_nothing(self):
        self.assertEqual(ensure_citations("Kasimir est un elfe.", []), "Kasimir est un elfe.")


class LoadKnowledgeTest(unittest.TestCase):
    def test_missing_file_gives_empty_list(self):
        self.assertEqual(load_knowledge("fichier_inexistant.json"), [])


if __name__ == "__main__":
    unittest.main()
