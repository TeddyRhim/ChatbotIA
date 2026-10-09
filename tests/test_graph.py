import unittest

from graph import bridges, build_adjacency, build_name_index, neighbors
from knowledge import cited_numbers
from main import Chatbot


def fiche(name, text, section="PERSONNAGES", aliases=(), liens=()):
    return {"section": section, "subsection": name, "aliases": list(aliases),
            "liens": list(liens), "text": f"Faits : {text}"}


KNOWLEDGE = [
    fiche("Elowen", "Gardienne de la tour de Vélan, amie de Maren", aliases=["la Gardienne"]),  # 0
    fiche("Maren", "Roi d'Aldoria, frère d'Elowen"),                                              # 1
    fiche("Korrin", "Chef des brigands, cherche le Cristal d'aube", aliases=["le Borgne"]),       # 2
    fiche("Cristal d'aube", "Gemme convoitée, cachée dans la tour de Vélan", section="OBJETS"),   # 3
    fiche("Tour de Vélan", "Tour de pierre blanche", section="LIEUX"),                            # 4
    fiche("Arc 1", "Elowen et Korrin se rencontrent", section="JOURNAL", aliases=["Elowen"]),     # 5
]


class NameIndexTest(unittest.TestCase):
    def test_primary_name_beats_alias_and_summary_fiches_are_not_targets(self):
        index = build_name_index(KNOWLEDGE)
        self.assertEqual(index["elowen"], 0)
        self.assertEqual(index["le borgne"], 2)

    def test_ambiguous_alias_is_ignored(self):
        knowledge = [fiche("Alpha", "x", aliases=["Grand Roi"]), fiche("Bêta", "y", aliases=["Grand Roi"])]
        self.assertNotIn("grand roi", build_name_index(knowledge))


class AdjacencyTest(unittest.TestCase):
    def test_mentions_create_symmetric_links_ignoring_accents_and_case(self):
        adjacency = build_adjacency(KNOWLEDGE)
        self.assertEqual(adjacency[0], {1, 4})          # Elowen cite Maren et la tour de Velan
        self.assertIn(0, adjacency[1])                  # Maren cite Elowen : lien symétrique
        self.assertEqual(adjacency[3], {2, 4})  # cité par Korrin et lié à la tour

    def test_summary_fiches_have_no_links(self):
        self.assertEqual(build_adjacency(KNOWLEDGE)[5], set())

    def test_explicit_lie_field(self):
        knowledge = [fiche("Alpha", "rien", liens=["Bêta"]), fiche("Bêta", "autre")]
        self.assertEqual(build_adjacency(knowledge)[0], {1})

    def test_no_match_inside_longer_word(self):
        knowledge = [fiche("Rose", "fleur"), fiche("Autre", "il arrose le jardin")]
        self.assertEqual(build_adjacency(knowledge)[1], set())


class NeighborsAndBridgesTest(unittest.TestCase):
    def test_neighbors_exclude_hits_and_prefer_relevant_ones(self):
        adjacency = {0: {1, 2, 3}, 1: {0}, 2: {0}, 3: {0}}
        self.assertEqual(neighbors([0], adjacency, extra=1, preferred=[3]), [3])
        self.assertNotIn(0, neighbors([0], adjacency, extra=5, exclude={1}))

    def test_bridges_link_unlinked_pairs_with_common_neighbors(self):
        adjacency = build_adjacency(KNOWLEDGE)
        pairs = [(a, b) for _, a, b, _ in bridges([0, 2, 3], adjacency)]
        self.assertIn((0, 3), pairs)       # Elowen et le Cristal : non liés, tous deux liés à la tour
        self.assertNotIn((0, 1), pairs)    # Elowen et Maren sont déjà liés


class CitationTest(unittest.TestCase):
    def test_cited_numbers_in_order_without_duplicates(self):
        self.assertEqual(cited_numbers("a [2] b [1] c [2]"), [2, 1])

    def test_grouped_citations_are_read(self):
        self.assertEqual(cited_numbers("a [1, 8] b [3][1] c [4; 5]"), [1, 8, 3, 4, 5])

    def test_sources_only_list_cited_fiches(self):
        out = Chatbot._with_sources("Réponse [2].", KNOWLEDGE[:3])
        self.assertIn("[2] [PERSONNAGES > Maren]", out)
        self.assertNotIn("Elowen]", out)
        self.assertEqual(Chatbot._with_sources("Pas de citation", KNOWLEDGE[:3]), "Pas de citation")

    def test_unsourced_piste_is_flagged(self):
        text = "Piste 1 : A lié à B. Justification : [1].\n\nPiste 2 : C lié à D sans source.\n"
        out = Chatbot._flag_unsourced(text, n_fragments=3)
        self.assertEqual(out.count("Attention :"), 1)
        self.assertLess(out.index("Piste 2"), out.index("Attention :"))


if __name__ == "__main__":
    unittest.main()
