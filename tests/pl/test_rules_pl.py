import unittest
from coreferee.rules import RulesAnalyzerFactory
from coreferee.test_utils import get_nlps
from coreferee.data_model import Mention

nlps = get_nlps("pl")
train_version_mismatch = False
for nlp in nlps:
    if not nlp.meta["matches_train_version"]:
        train_version_mismatch = True
train_version_mismatch_message = (
    "Loaded model version does not match train model version"
)


class PolishRulesTest(unittest.TestCase):
    def setUp(self):

        self.nlps = get_nlps("pl")
        self.rules_analyzers = [
            RulesAnalyzerFactory.get_rules_analyzer(nlp) for nlp in self.nlps
        ]

    def all_nlps(self, func):
        for nlp in self.nlps:
            func(nlp)

    def compare_get_dependent_sibling_info(
        self,
        doc_text,
        index,
        expected_dependent_siblings,
        expected_governing_sibling,
        expected_has_or_coordination,
        *,
        excluded_nlps=[]
    ):
        def func(nlp):

            if nlp.meta["name"] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            self.assertEqual(
                expected_dependent_siblings,
                str(doc[index]._.coref_chains.temp_dependent_siblings),
                nlp.meta["name"],
            )
            for sibling in (
                sibling
                for sibling in doc[index]._.coref_chains.temp_dependent_siblings
                if sibling.i != index
            ):
                self.assertEqual(
                    doc[index],
                    sibling._.coref_chains.temp_governing_sibling,
                    nlp.meta["name"],
                )
            if expected_governing_sibling is None:
                self.assertEqual(
                    None,
                    doc[index]._.coref_chains.temp_governing_sibling,
                    nlp.meta["name"],
                )
            else:
                self.assertEqual(
                    doc[expected_governing_sibling],
                    doc[index]._.coref_chains.temp_governing_sibling,
                    nlp.meta["name"],
                )
            self.assertEqual(
                expected_has_or_coordination,
                doc[index]._.coref_chains.temp_has_or_coordination,
                nlp.meta["name"],
            )

        self.all_nlps(func)

    def test_get_dependent_sibling_info_no_conjunction(self):
        self.compare_get_dependent_sibling_info(
            "Richard poszed?? do domu", 0, "[]", None, False
        )

    def test_get_dependent_sibling_info_two_member_conjunction_phrase_and(self):
        self.compare_get_dependent_sibling_info(
            "Richard i Christine poszli do domu", 0, "[Christine]", None, False
        )

    def test_get_dependent_sibling_info_two_member_conjunction_phrase_with(self):
        self.compare_get_dependent_sibling_info(
            "Richard z synem poszli do domu",
            0,
            "[synem]",
            None,
            False,
            excluded_nlps=["core_news_sm"],
        )

    def test_get_dependent_sibling_info_two_member_conjunction_phrase_verb_anaphor_with(
        self,
    ):
        self.compare_get_dependent_sibling_info(
            "Tomek przyjecha??. Wyszed?? z Ann??",
            3,
            "[Ann??]",
            None,
            False,
            excluded_nlps=["core_news_md", "core_news_sm"],
        )

    def test_get_dependent_sibling_info_two_member_conjunction_phrase_verb_anaphor_with_control_1(
        self,
    ):
        self.compare_get_dependent_sibling_info(
            "Tomek przyjecha??. Wyszed?? codziennie z Ann??", 3, "[]", None, False
        )

    def test_get_dependent_sibling_info_two_member_conjunction_phrase_verb_anaphor_with_control_2(
        self,
    ):
        self.compare_get_dependent_sibling_info(
            "Tomek przyjecha??. On wyszed?? z Ann??", 3, "[]", None, False
        )

    def test_get_dependent_sibling_info_two_member_conjunction_phrase_verb_anaphor_with_and(
        self,
    ):
        self.compare_get_dependent_sibling_info(
            "Tomek przyjecha??. Wyszed?? z Ann?? i Agnieszk??",
            3,
            "[Ann??, Agnieszk??]",
            None,
            False,
            excluded_nlps=["core_news_md"],
        )

    def test_get_dependent_sibling_info_two_member_conjunction_phrase_with_same_parent(
        self,
    ):
        self.compare_get_dependent_sibling_info(
            "Widzia?? psa z psem.", 1, "[psem]", None, False
        )

    def test_get_dependent_sibling_info_two_member_conjunction_phrase_with_same_parent_contrl(
        self,
    ):
        self.compare_get_dependent_sibling_info(
            "Widzia?? psa ju?? z psem.", 1, "[]", None, False
        )

    def test_get_governing_sibling_info_two_member_conjunction_phrase_and(self):
        self.compare_get_dependent_sibling_info(
            "Richard i Christine poszli do domu", 2, "[]", 0, False
        )

    def test_get_dependent_sibling_info_three_member_conjunction_phrase_with_comma_and(
        self,
    ):
        self.compare_get_dependent_sibling_info(
            "Carol, Richard i Ralf mieli zebranie.",
            0,
            "[Richard, Ralf]",
            None,
            False,
            excluded_nlps=["core_news_md", "core_news_sm"],
        )

    def test_get_dependent_sibling_info_conjunction_itself(self):
        self.compare_get_dependent_sibling_info(
            "Zebranie z Carolem i Ralfem i Richardem mia??o miejsce wczoraj.",
            3,
            "[]",
            None,
            False,
        )

    def test_get_dependent_sibling_info_dependent_sibling(self):
        self.compare_get_dependent_sibling_info(
            "Zebranie z Carolem i Ralfem i Richardem mia??o miejsce wczoraj.",
            4,
            "[]",
            0,
            False,
        )

    def test_get_dependent_sibling_other_instrumental(self):
        self.compare_get_dependent_sibling_info(
            "Rozmawiali o opinii nad t?? ustaw??.", 5, "[]", None, False
        )

    def compare_independent_noun(
        self, doc_text, expected_per_indexes, *, excluded_nlps=[]
    ):
        def func(nlp):

            if nlp.meta["name"] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            per_indexes = [
                token.i for token in doc if rules_analyzer.is_independent_noun(token)
            ]
            self.assertEqual(expected_per_indexes, per_indexes, nlp.meta["name"])

        self.all_nlps(func)

    def test_independent_noun_simple(self):
        self.compare_independent_noun("Poogl??dali sobie wielkie lwy.", [3])

    def test_independent_noun_conjunction(self):
        self.compare_independent_noun(
            "Poogl??dali sobie wielkie lwy, w????e, i s??onie",
            [3, 5, 8],
            excluded_nlps=["core_news_sm"],
        )

    @unittest.skipIf(train_version_mismatch, train_version_mismatch_message)
    def test_substituting_indefinite_pronoun(self):
        self.compare_independent_noun("Jeden z ch??opc??w przyszed?? do domu", [2, 5])

    def test_blacklisted(self):
        self.compare_independent_noun(
            "Moim zdaniem bywa ch??opiec na przyk??ad zawsze zm??czony", [3]
        )

    def test_blacklisted_control(self):
        self.compare_independent_noun("Moim zdaniem jest to dobry przyk??ad.", [5])

    def test_punctuation(self):
        self.compare_independent_noun("[Enter]", [1])

    def compare_potentially_indefinite(
        self, doc_text, index, expected_truth, *, excluded_nlps=[]
    ):
        def func(nlp):

            if nlp.meta["name"] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            self.assertEqual(
                expected_truth,
                rules_analyzer.is_potentially_indefinite(doc[index]),
                nlp.meta["name"],
            )

        self.all_nlps(func)

    def test_potentially_indefinite_proper_noun(self):
        self.compare_potentially_indefinite("Rozmawia??em z Piotrem", 2, False)

    def test_potentially_indefinite_common_noun(self):
        self.compare_potentially_indefinite("Rozmawia??em z bratem", 2, True)

    def test_potentially_indefinite_common_noun_jakis(self):
        self.compare_potentially_indefinite(
            "Rozmawia??em z jakim?? bratem", 3, True, excluded_nlps=["core_news_md"]
        )

    def test_potentially_indefinite_definite_common_noun(self):
        self.compare_potentially_indefinite(
            "Rozmawia??em z tym bratem", 3, False, excluded_nlps=["core_news_sm"]
        )

    def test_potentially_indefinite_common_noun_with_possessive_pronoun(self):
        self.compare_potentially_indefinite("Rozmawia??em z naszym bratem", 3, False)

    def compare_potentially_definite(
        self, doc_text, index, expected_truth, *, excluded_nlps=[]
    ):
        def func(nlp):

            if nlp.meta["name"] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            self.assertEqual(
                expected_truth,
                rules_analyzer.is_potentially_definite(doc[index]),
                nlp.meta["name"],
            )

        self.all_nlps(func)

    def test_potentially_definite_proper_noun(self):
        self.compare_potentially_definite("Rozmawia??em z Piotrem", 2, False)

    def test_potentially_definite_common_noun(self):
        self.compare_potentially_definite("Rozmawia??em z bratem", 2, True)

    def test_potentially_definite_definite_common_noun(self):
        self.compare_potentially_definite("Rozmawia??em z tym bratem", 3, True)

    def test_potentially_definite_common_noun_with_possessive_pronoun(self):
        self.compare_potentially_definite("Rozmawia??em z naszym bratem", 3, True)

    def test_potentially_definite_common_noun_jakis(self):
        self.compare_potentially_definite("Rozmawia??em z jakim?? bratem", 3, False)

    def compare_potential_anaphor(
        self, doc_text, expected_per_indexes, *, excluded_nlps=[]
    ):
        def func(nlp):

            if nlp.meta["name"] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            per_indexes = [
                token.i for token in doc if rules_analyzer.is_potential_anaphor(token)
            ]
            self.assertEqual(expected_per_indexes, per_indexes, nlp.meta["name"])

        self.all_nlps(func)

    def test_third_person_pronouns(self):
        self.compare_potential_anaphor(
            "Kobieta powo??a??a go i pokaza??a mu jego samoch??d i sw??j samoch??d.",
            [2, 5, 6, 9],
        )

    def test_third_person_pronouns_full_forms(self):
        self.compare_potential_anaphor(
            "Kobieta powo??a??a jego i pokaza??a jemu jego samoch??d i sw??j samoch??d.",
            [2, 5, 6, 9],
        )

    def test_first_and_second_person_pronouns(self):
        self.compare_potential_anaphor("Ja wiem, ??e ty go znasz", [5])

    @unittest.skipIf(train_version_mismatch, train_version_mismatch_message)
    def test_reflexive_non_clitic(self):
        self.compare_potential_anaphor(
            "Wtedy umy?? sobie z??by i siebie zobaczy?? w lustrze.", [1, 2, 5, 6]
        )

    @unittest.skipIf(train_version_mismatch, train_version_mismatch_message)
    def test_reflexive_clitic(self):
        self.compare_potential_anaphor(
            "Wtedy umy?? sobie z??by i zobaczy?? si?? w lustrze.", [1, 2, 5]
        )

    def test_verb_imperfective_past(self):
        self.compare_potential_anaphor("Jecha??a do domu.", [0])

    def test_verb_perfective_past(self):
        self.compare_potential_anaphor("Posz??a do domu.", [0])

    def test_verb_imperfective_present(self):
        self.compare_potential_anaphor("Idzie do domu.", [0])

    def test_verb_imperfective_present_control_1(self):
        self.compare_potential_anaphor("Dziecko idzie do domu.", [])

    def test_verb_imperfective_present_control_2(self):
        self.compare_potential_anaphor("Dziecko zostaje przyj??te do domu.", [])

    def test_verb_perfective_future(self):
        self.compare_potential_anaphor("P??jdzie do domu.", [0])

    def test_verb_imperfective_future(self):
        self.compare_potential_anaphor("B??dzie jecha?? do domu.", [0])

    def test_verb_imperfective_future_control(self):
        self.compare_potential_anaphor("Dziecko b??dzie jecha?? do domu.", [])

    def test_verb_frequentative_present_non_motion_verb(self):
        self.compare_potential_anaphor("Bywa w domu.", [0])

    def test_verb_frequentative_present_motion_verb(self):
        self.compare_potential_anaphor("Chodzi do szko??y.", [0])

    def test_verb_conditional(self):
        self.compare_potential_anaphor("Wtedy poszed??by do szko??y.", [1])

    def test_verb_conditional_split(self):
        self.compare_potential_anaphor(
            "By poszed?? do szko??y.", [1], excluded_nlps=["core_news_md"]
        )

    def test_verb_modal_and_control_imperfective_infinitive(self):
        self.compare_potential_anaphor("Chce i???? do szko??y.", [0])

    def test_verb_modal_and_control_imperfective_infinitive_with_conjunction(self):
        self.compare_potential_anaphor("Chce i b??dzie i???? do szko??y.", [0, 2])

    def test_verb_modal_and_control_imperfective_infinitive_control(self):
        self.compare_potential_anaphor("Dziecko chce i???? do szko??y.", [])

    def test_verb_modal_and_control_perfective_infinitive(self):
        self.compare_potential_anaphor("Chcia??by p??j???? do szko??y.", [0])

    def test_verb_auxiliary(self):
        self.compare_potential_anaphor("Zosta?? powitany w nowej szkole.", [0])

    def test_verb_control_1_2_persons(self):
        self.compare_potential_anaphor(
            "Mam, masz, ma, mamy, macie, maj?? idee.", [4, 10]
        )

    def test_verb_impersonal_present(self):
        self.compare_potential_anaphor("Okazuje si??, ??e to nieprawda.", [])

    def test_verb_impersonal_past(self):
        self.compare_potential_anaphor("Okaza??o si??, ??e to nieprawda.", [])

    def test_verb_impersonal_past_control(self):
        self.compare_potential_anaphor("Okaza??a si??, ??e to nieprawda.", [0])

    def compare_potential_pair(
        self,
        doc_text,
        referred_index,
        include_dependent_siblings,
        referring_index,
        expected_truth,
        *,
        excluded_nlps=[],
        directly=True
    ):
        def func(nlp):

            if nlp.meta["name"] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            assert rules_analyzer.is_independent_noun(
                doc[referred_index]
            ) or rules_analyzer.is_potential_anaphor(doc[referred_index])
            assert rules_analyzer.is_potential_anaphor(doc[referring_index])
            referred_mention = Mention(doc[referred_index], include_dependent_siblings)
            self.assertEqual(
                expected_truth,
                rules_analyzer.is_potential_anaphoric_pair(
                    referred_mention, doc[referring_index], directly
                ),
                nlp.meta["name"],
            )

        self.all_nlps(func)

    def test_third_person_pronouns(self):
        self.compare_potential_pair(
            "Wysz??a, ??eby rzuci?? okiem na jej samoch??d.", 0, False, 6, 2
        )

    def test_third_person_verbs(self):
        self.compare_potential_pair("Wysz??a. Krzykn????a.", 0, False, 2, 2)

    def test_masculine_pronoun(self):
        self.compare_potential_pair(
            "Ch??opiec wszed??. On by?? szcz????liwy.", 0, False, 3, 2
        )

    def test_masculine_pronoun_control_gender(self):
        self.compare_potential_pair(
            "Ch??opiec wszed??. Ona by??a szcz????liwa.", 0, False, 3, 0
        )

    def test_masculine_pronoun_control_number(self):
        self.compare_potential_pair(
            "Ch??opiec wszed??. One by??y szcz????liwe.", 0, False, 3, 0
        )

    def test_masculine_verb_marked(self):
        self.compare_potential_pair("Ch??opiec wszed??. Szcz????liwy by??.", 0, False, 4, 2)

    def test_masculine_verb_not_marked(self):
        self.compare_potential_pair("Ch??opiec wszed??. Szcz????liwy jest.", 0, False, 4, 2)

    def test_masculine_verb_control_gender(self):
        self.compare_potential_pair("Ch??opiec wszed??. Potem wysz??o.", 0, False, 4, 0)

    def test_masculine_verb_control_number(self):
        self.compare_potential_pair("Ch??opiec wszed??. Szcz????liwi byli.", 0, False, 4, 0)

    def test_masculine_reflexive_possessive(self):
        self.compare_potential_pair("Ch??opiec zobaczy?? swojego psa.", 0, False, 2, 2)

    def test_masculine_nonreflexive_possessive(self):
        self.compare_potential_pair(
            "Ch??opiec zobaczy?? jego psa.",
            0,
            False,
            2,
            2,
            excluded_nlps=["core_news_sm"],
        )

    def test_masculine_nonreflexive_possessive_control(self):
        self.compare_potential_pair("Ch??opiec zobaczy?? te?? jej psa.", 0, False, 3, 0)

    def test_feminine_pronoun(self):
        self.compare_potential_pair(
            "Dziewczyna wesz??a. Ona by??a szcz????liwa.", 0, False, 3, 2
        )

    def test_feminine_pronoun_control_gender(self):
        self.compare_potential_pair(
            "Dziewczyna wesz??a. On by?? szcz????liwy.", 0, False, 3, 0
        )

    def test_feminine_pronoun_control_number(self):
        self.compare_potential_pair(
            "Dziewczyna wesz??a. Oni byli szcz????liwi.", 0, False, 3, 0
        )

    def test_feminine_verb_marked(self):
        self.compare_potential_pair(
            "Dziewczyna wesz??a. Szcz????liwa by??a.", 0, False, 4, 2
        )

    def test_feminine_verb_not_marked(self):
        self.compare_potential_pair(
            "Dziewczyna wesz??a. Szcz????liwa jest.", 0, False, 4, 2
        )

    def test_feminine_verb_control_gender(self):
        self.compare_potential_pair(
            "Dziewczyna wesz??a. Szcz????liwy by??.", 0, False, 4, 0
        )

    def test_feminine_verb_control_number(self):
        self.compare_potential_pair("Dziewczyna wesz??a. Potem wysz??y.", 0, False, 4, 0)

    def test_feminine_reflexive_possessive(self):
        self.compare_potential_pair("Dziewczyna zobaczy??a swojego psa.", 0, False, 2, 2)

    def test_feminine_nonreflexive_possessive(self):
        self.compare_potential_pair("Dziewczyna zobaczy??a te?? jej psa.", 0, False, 3, 2)

    def test_feminine_nonreflexive_possessive_control(self):
        self.compare_potential_pair("Dziewczyna zobaczy??a jego psa.", 0, False, 2, 0)

    def test_neuter_pronoun_1(self):
        self.compare_potential_pair(
            "Dziecko wesz??o. Ono by??o szcz????liwe.", 0, False, 3, 2
        )

    def test_neuter_pronoun_2(self):
        self.compare_potential_pair(
            "Dziecko wesz??o. Widzieli go.",
            0,
            False,
            4,
            2,
            excluded_nlps=["core_news_sm"],
        )

    def test_neuter_pronoun_3(self):
        self.compare_potential_pair(
            "Dziecko wesz??o. Pomogli mu.",
            0,
            False,
            4,
            2,
            excluded_nlps=["core_news_sm"],
        )

    def test_neuter_pronoun_control_gender(self):
        self.compare_potential_pair(
            "Dziecko wesz??o. Ona by??a szcz????liwa.", 0, False, 3, 0
        )

    def test_neuter_pronoun_control_number(self):
        self.compare_potential_pair(
            "Dziecko wesz??o. Oni byli szcz????liwi.", 0, False, 3, 0
        )

    def test_neuter_verb_marked(self):
        self.compare_potential_pair("Dziecko wesz??o. Potem wysz??o.", 0, False, 4, 2)

    def test_neuter_verb_not_marked(self):
        self.compare_potential_pair("Dziecko wesz??o. Szcz????liwe jest.", 0, False, 4, 2)

    def test_neuter_verb_control_gender(self):
        self.compare_potential_pair("Dziecko wesz??o. Szcz????liwy by??.", 0, False, 4, 0)

    def test_neuter_verb_control_number(self):
        self.compare_potential_pair("Dziecko wesz??o. Szcz????liwi byli.", 0, False, 4, 0)

    def test_neuter_reflexive_possessive(self):
        self.compare_potential_pair("Dziecko zobaczy??o swojego psa.", 0, False, 2, 2)

    def test_neuter_nonreflexive_possessive(self):
        self.compare_potential_pair("Dziecko zobaczy??o jego psa.", 0, False, 2, 2)

    def test_virile_pronoun(self):
        self.compare_potential_pair(
            "Faceci weszli. Oni byli szcz????liwi.", 0, False, 3, 2
        )

    def test_virile_pronoun_control_gender(self):
        self.compare_potential_pair(
            "Faceci weszli. One by??y szcz????liwe.", 0, False, 3, 0
        )

    def test_virile_pronoun_control_number(self):
        self.compare_potential_pair("Faceci weszli. On by?? szcz????liwy.", 0, False, 3, 0)

    def test_virile_verb_marked(self):
        self.compare_potential_pair("Faceci weszli. Szcz????liwi byli.", 0, False, 4, 2)

    def test_virile_verb_not_marked(self):
        self.compare_potential_pair(
            "Faceci weszli. Szcz????liwi s??.",
            0,
            False,
            4,
            2,
            excluded_nlps=["core_news_sm"],
        )

    def test_virile_verb_control_gender(self):
        self.compare_potential_pair(
            "Faceci weszli. Szcz????liwe by??y.",
            0,
            False,
            4,
            0,
            excluded_nlps=["core_news_sm"],
        )

    def test_virile_verb_control_number(self):
        self.compare_potential_pair(
            "Faceci weszli. Szcz????liwa by??a.",
            0,
            False,
            4,
            0,
            excluded_nlps=["core_news_sm"],
        )

    def test_virile_reflexive_possessive(self):
        self.compare_potential_pair("Faceci zobaczyli swojego psa.", 0, False, 2, 2)

    def test_virile_nonreflexive_possessive(self):
        self.compare_potential_pair(
            "Faceci zobaczyli ich psa.", 0, False, 2, 2, excluded_nlps=["core_news_md"]
        )

    def test_nonvirile_pronoun_1(self):
        self.compare_potential_pair(
            "Kobiety wesz??y. One by??y szcz????liwe.", 0, False, 3, 2
        )

    def test_nonvirile_pronoun_2(self):
        self.compare_potential_pair("Psy wesz??y. One by??y szcz????liwe.", 0, False, 3, 2)

    def test_nonvirile_pronoun_3(self):
        self.compare_potential_pair("Domy wesz??y. One by??y szcz????liwe.", 0, False, 3, 2)

    def test_nonvirile_pronoun_4(self):
        self.compare_potential_pair(
            "Dzieci wesz??y. One by??y szcz????liwe.", 0, False, 3, 2
        )

    def test_nonvirile_pronoun_control_gender(self):
        self.compare_potential_pair(
            "Kobiety wesz??y. Oni byli szcz????liwi.", 0, False, 3, 0
        )

    def test_nonvirile_pronoun_control_number(self):
        self.compare_potential_pair(
            "Kobiety wesz??y. Ona by??a szcz????liwa.", 0, False, 3, 0
        )

    def test_nonvirile_verb_marked_1(self):
        self.compare_potential_pair(
            "Kobiety wesz??y. Szcz????liwe by??y.",
            0,
            False,
            4,
            2,
            excluded_nlps=["core_news_sm"],
        )

    def test_nonvirile_verb_marked_2(self):
        self.compare_potential_pair("Psy wesz??y. Szcz????liwe by??y.", 0, False, 4, 2)

    def test_nonvirile_verb_marked_3(self):
        self.compare_potential_pair("Domy wesz??y. Szcz????liwe by??y.", 0, False, 4, 2)

    def test_nonvirile_verb_marked_4(self):
        self.compare_potential_pair("Dzieci wesz??y. Szcz????liwe by??y.", 0, False, 4, 2)

    def test_nonvirile_verb_not_marked(self):
        self.compare_potential_pair(
            "Kobiety weszly. Szcz????liwe s??.",
            0,
            False,
            4,
            2,
            excluded_nlps=["core_news_sm"],
        )

    def test_nonvirile_verb_control_gender(self):
        self.compare_potential_pair("Kobiety wesz??y. Szcz????liwi byli.", 0, False, 4, 0)

    def test_nonvirile_verb_control_number(self):
        self.compare_potential_pair(
            "Kobiety wesz??y. Szcz????liwa by??a.",
            0,
            False,
            4,
            0,
            excluded_nlps=["core_news_sm"],
        )

    def test_nonvirile_reflexive_possessive(self):
        self.compare_potential_pair("Kobiety zobaczy??y swojego psa.", 0, False, 2, 2)

    def test_nonvirile_nonreflexive_possessive(self):
        self.compare_potential_pair(
            "Kobiety zobaczy??y ich psa.",
            0,
            False,
            2,
            2,
            excluded_nlps=["core_news_md", "core_news_sm"],
        )

    def test_male_name(self):
        self.compare_potential_pair(
            "Krzysiek widzi niebo. On jest szcz????liwy.", 0, False, 4, 2
        )

    def test_male_name_control(self):
        self.compare_potential_pair(
            "Krzysiek widzi niebo. Ona jest szcz????liwa.", 0, False, 4, 0
        )

    def test_female_name(self):
        self.compare_potential_pair(
            "Anna widzi niebo. Ona jest szcz????liwa.", 0, False, 4, 2
        )

    def test_female_name_control(self):
        self.compare_potential_pair(
            "Anna widzi niebo. On jest szcz????liwy.", 0, False, 4, 0
        )

    def test_coordinated_phrase_two_personal_masculine(self):
        self.compare_potential_pair(
            "S?? syn i ojciec. Oni s?? szcz????liwi.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_personal_masculine_control(self):
        self.compare_potential_pair(
            "S?? syn i ojciec. One s?? szcz????liwe.", 1, True, 5, 0
        )

    def test_coordinated_phrase_two_animal_masculine(self):
        self.compare_potential_pair(
            "S?? pies i lew. One s?? szcz????liwe.",
            1,
            True,
            5,
            2,
            excluded_nlps=["core_news_sm"],
        )

    def test_coordinated_phrase_two_animal_masculine_control(self):
        self.compare_potential_pair(
            "S?? pies i lew. Oni s?? szcz????liwi.",
            1,
            True,
            5,
            0,
            excluded_nlps=["core_news_sm"],
        )

    def test_coordinated_phrase_two_object_masculine(self):
        self.compare_potential_pair(
            "S?? dom i samoch??d. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_object_masculine_control(self):
        self.compare_potential_pair(
            "S?? dom i samoch??d. Oni s?? szcz????liwi.", 1, True, 5, 0
        )

    def test_coordinated_phrase_two_object_masculine_z(self):
        self.compare_potential_pair(
            "S?? dom z samochodem. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_object_masculine_z_control(self):
        self.compare_potential_pair(
            "S?? dom z samochodem. Oni s?? szcz????liwi.", 1, True, 5, 0
        )

    def test_coordinated_phrase_two_object_feminine(self):
        self.compare_potential_pair(
            "S?? mama i c??rka. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_object_feminine_control(self):
        self.compare_potential_pair(
            "S?? mama i c??rka. Oni s?? szcz????liwi.", 1, True, 5, 0
        )

    def test_coordinated_phrase_two_object_neuter(self):
        self.compare_potential_pair(
            "S?? dziecko i dziecko. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_object_neuter_control(self):
        self.compare_potential_pair(
            "S?? dziecko i dziecko. Oni s?? szcz????liwi.", 1, True, 5, 0
        )

    def test_coordinated_phrase_two_plural_personal_masculine(self):
        self.compare_potential_pair(
            "S?? synowie i ojciec. Oni s?? szcz????liwi.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_plural_personal_masculine_control(self):
        self.compare_potential_pair(
            "S?? synowie i ojciec. One s?? szcz????liwe.", 1, True, 5, 0
        )

    def test_coordinated_phrase_two_personal_masculine_mixed(self):
        self.compare_potential_pair("S?? syn i c??rka. Oni s?? szcz????liwi.", 1, True, 5, 2)

    def test_coordinated_phrase_two_personal_masculine_mixed(self):
        self.compare_potential_pair("S?? syn i c??rki. One s?? szcz????liwe.", 1, True, 5, 0)

    def test_coordinated_phrase_two_plural_personal_masculine_mixed(self):
        self.compare_potential_pair(
            "S?? synowie i c??rki. Oni s?? szcz????liwi.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_plural_personal_masculine_mixed(self):
        self.compare_potential_pair(
            "S?? synowie i c??rka. One s?? szcz????liwe.", 1, True, 5, 0
        )

    def test_coordinated_phrase_two_plural_animal_masculine(self):
        self.compare_potential_pair("S?? psy i lwy. One s?? szcz????liwe.", 1, True, 5, 2)

    def test_coordinated_phrase_two_plural_animal_masculine_control(self):
        self.compare_potential_pair(
            "S?? psy i lwy. Oni s?? szcz????liwi.",
            1,
            True,
            5,
            0,
            excluded_nlps=["core_news_sm"],
        )

    def test_coordinated_phrase_two_masculine_animal_and_object(self):
        self.compare_potential_pair("S?? pies i dom. One s?? szcz????liwe.", 1, True, 5, 2)

    def test_coordinated_phrase_two_masculine_animal_and_object_control(self):
        self.compare_potential_pair("S?? pies i dom. Oni s?? szcz????liwi.", 1, True, 5, 0)

    def test_coordinated_phrase_two_feminine(self):
        self.compare_potential_pair(
            "S?? kobieta i c??rka. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_feminine_control(self):
        self.compare_potential_pair(
            "S?? kobieta i c??rka. Oni s?? szcz????liwi.", 1, True, 5, 0
        )

    def test_coordinated_phrase_two_neuter(self):
        self.compare_potential_pair(
            "S?? dziecko i dziecko. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_neuter_control(self):
        self.compare_potential_pair(
            "S?? dziecko i dziecko. Oni s?? szcz????liwi.", 1, True, 5, 0
        )

    def test_coordinated_phrase_two_masculine_animal_feminine_mix_1(self):
        self.compare_potential_pair(
            "S?? pies i kobieta. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_animal_feminine_mix_2(self):
        self.compare_potential_pair(
            "S?? pies i kobieta. Oni s?? szcz????liwi.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_animal_feminine_mix_3(self):
        self.compare_potential_pair(
            "S?? psy i kobiety. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_animal_feminine_mix_4(self):
        self.compare_potential_pair(
            "S?? psy i kobiety. Oni s?? szcz????liwi.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_animal_feminine_z_mix_1(self):
        self.compare_potential_pair(
            "S?? psy z kobietami. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_animal_feminine_z_mix_2(self):
        self.compare_potential_pair(
            "S?? psy z kobietami. Oni s?? szcz????liwi.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_object_feminine_mix_1(self):
        self.compare_potential_pair(
            "S?? dom i kobieta. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_object_feminine_mix_2(self):
        self.compare_potential_pair(
            "S?? dom i kobieta. Oni s?? szcz????liwi.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_object_feminine_mix_3(self):
        self.compare_potential_pair(
            "S?? domy i kobiety. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_object_feminine_mix_4(self):
        self.compare_potential_pair(
            "S?? domy i kobiety. Oni s?? szcz????liwi.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_animal_neuter_mix_1(self):
        self.compare_potential_pair(
            "S?? pies i dziecko. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_animal_neuter_mix_2(self):
        self.compare_potential_pair(
            "S?? pies i dziecko. Oni s?? szcz????liwi.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_animal_neuter_mix_3(self):
        self.compare_potential_pair(
            "S?? psy i dzieci. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_animal_neuter_mix_4(self):
        self.compare_potential_pair(
            "S?? psy i dzieci. Oni s?? szcz????liwi.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_object_neuter_mix_1(self):
        self.compare_potential_pair(
            "S?? dom i dziecko. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_object_neuter_mix_2(self):
        self.compare_potential_pair(
            "S?? dom i dziecko. Oni s?? szcz????liwi.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_object_neuter_mix_3(self):
        self.compare_potential_pair(
            "S?? domy i dzieci. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_masculine_object_neuter_mix_4(self):
        self.compare_potential_pair(
            "S?? domy i dzieci. Oni s?? szcz????liwi.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_feminine_neuter_mix_1(self):
        self.compare_potential_pair(
            "S?? kobieta i dziecko. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_feminine_neuter_mix_2(self):
        self.compare_potential_pair(
            "S?? kobieta i dziecko. Oni s?? szcz????liwi.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_feminine_neuter_mix_3(self):
        self.compare_potential_pair(
            "S?? kobiety i dzieci. One s?? szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_feminine_neuter_mix_4(self):
        self.compare_potential_pair(
            "S?? kobiety i dzieci. Oni s?? szcz????liwi.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_feminine_neuter_mix_verb_virile(self):
        self.compare_potential_pair(
            "Przyszli kobiety i dzieci. Oni byli szcz????liwi.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_feminine_neuter_mix_verb_virile_control(self):
        self.compare_potential_pair(
            "Przyszli kobiety i dzieci. One by??y szcz????liwe.",
            1,
            True,
            5,
            0,
            excluded_nlps=["core_news_sm"],
        )

    def test_coordinated_phrase_two_feminine_neuter_mix_verb_nonvirile(self):
        self.compare_potential_pair(
            "Przysz??y kobiety i dzieci. One by??y szcz????liwe.", 1, True, 5, 2
        )

    def test_coordinated_phrase_two_feminine_neuter_mix_verb_nonvirile_control(self):
        self.compare_potential_pair(
            "Przyjecha??y kobiety i dzieci. Oni byli szcz????liwi.",
            1,
            True,
            5,
            0,
            excluded_nlps=["core_news_sm"],
        )

    def test_coordinated_phrase_two_plural_personal_masculine_mixed_only_feminine(self):
        self.compare_potential_pair(
            "S?? synowie i dziewczyny. One s?? szcz????liwe.",
            3,
            False,
            5,
            2,
            excluded_nlps=["core_news_sm"],
        )

    def test_coordinated_phrase_two_plural_personal_masculine_mixed_only_feminine_z(
        self,
    ):
        self.compare_potential_pair(
            "S?? synowie z dziewczynami. One s?? szcz????liwe.", 3, False, 5, 2
        )

    def test_coordinated_phrase_two_plural_personal_masculine_mixed_only_feminine_control(
        self,
    ):
        self.compare_potential_pair(
            "S?? synowie i dziewczyny. Oni s?? szcz????liwi.", 3, False, 5, 0
        )

    def test_coordinated_phrase_two_plural_personal_masculine_mixed_only_masculine(
        self,
    ):
        self.compare_potential_pair(
            "S?? synowie i dziewczyny. Oni s?? szcz????liwi.", 1, False, 5, 0
        )

    def test_coordinated_phrase_two_plural_personal_masculine_mixed_only_masculine_or(
        self,
    ):
        self.compare_potential_pair(
            "S?? synowie lub dziewczyny. Oni s?? szcz????liwi.", 1, False, 5, 2
        )

    def test_coordinated_phrase_two_plural_personal_masculine_mixed_only_masculine_z(
        self,
    ):
        self.compare_potential_pair(
            "S?? synowie z dziewczynami. Oni s?? szcz????liwi.", 1, False, 5, 0
        )

    def test_coordinated_phrase_singular_or_1(self):
        self.compare_potential_pair(
            "Jest syn albo c??rka. On jest szcz????liwy.", 1, True, 5, 2
        )

    def test_coordinated_phrase_singular_or_2(self):
        self.compare_potential_pair(
            "Jest syn albo c??rka. Ona jest szcz????liwa.",
            1,
            True,
            5,
            2,
            excluded_nlps=["core_news_md"],
        )

    def test_coordinated_phrase_singular_or_control_1(self):
        self.compare_potential_pair(
            "Jest syn albo c??rka. Ono jest szcz????liwe.", 1, True, 5, 0
        )

    def test_coordinated_phrase_singular_or_control_2(self):
        self.compare_potential_pair(
            "Jest syn albo c??rka. Oni s?? szcz????liwi.", 1, True, 5, 0
        )

    def test_coordinated_phrase_singular_or_control_3(self):
        self.compare_potential_pair(
            "Jest syn albo c??rka. One s?? szcz????liwe.", 1, True, 5, 0
        )

    def test_potential_pair_possessive_in_genitive_phrase_simple_nonreflexive_1(self):
        self.compare_potential_pair(
            "M???? jego kolegi przem??wi??", 0, False, 1, 0, excluded_nlps=["core_news_sm"]
        )

    def test_potential_pair_possessive_in_genitive_phrase_simple_nonreflexive_2(self):
        self.compare_potential_pair("M???? swojego kolegi przem??wi??", 0, False, 1, 0)

    def test_potential_pair_possessive_in_genitive_phrase_simple_not_directly(self):
        self.compare_potential_pair(
            "M???? jego kolegi przem??wi??", 0, False, 1, 2, directly=False
        )

    def test_potential_pair_possessive_in_genitive_phrase_coordination_head_nonreflexive(
        self,
    ):
        self.compare_potential_pair(
            "M???? z m????em jego kolegi przem??wili",
            0,
            False,
            3,
            2,
            excluded_nlps=["core_news_sm"],
        )

    def test_potential_pair_possessive_in_genitive_phrase_coordination_head_reflexive(
        self,
    ):
        self.compare_potential_pair(
            "Przyszed?? m???? z m????em swojego kolegi", 1, False, 4, 0
        )

    def test_potential_pair_possessive_in_genitive_phrase_control(self):
        self.compare_potential_pair("M???? z jego koleg?? przem??wili", 0, False, 2, 2)

    def test_potential_pair_possessive_in_genitive_phrase_double_simple(self):
        self.compare_potential_pair(
            "Przyszed?? m???? jego kolegi jego kolegi", 1, False, 4, 0
        )

    def test_potential_pair_possessive_in_genitive_phrase_double_control_1(self):
        self.compare_potential_pair(
            "Przyszed?? m???? z koleg?? jego kolegi", 1, False, 4, 2
        )

    def test_potential_pair_possessive_in_genitive_phrase_double_control_2(self):
        self.compare_potential_pair(
            "Przyszed?? m???? kolegi z jego koleg??",
            1,
            False,
            4,
            2,
            excluded_nlps=["core_news_md", "core_news_sm"],
        )

    def test_potential_pair_non_personal_subject_personal_verb(self):
        self.compare_potential_pair(
            "Dom sta??. Powiedzia??, wszystko dobrze.", 0, False, 3, 1
        )

    @unittest.skipIf(train_version_mismatch, train_version_mismatch_message)
    def test_potential_pair_non_personal_subject_personal_verb_control_conjunction(
        self,
    ):
        self.compare_potential_pair(
            "Dom i dom stoj??. One powiedzia??y, wszystko dobrze",
            0,
            True,
            5,
            1,
            excluded_nlps=["core_news_md", "core_news_sm"],
        )

    @unittest.skipIf(train_version_mismatch, train_version_mismatch_message)
    def test_potential_pair_non_personal_subject_personal_verb_control_z_conjunction(
        self,
    ):
        self.compare_potential_pair(
            "Dom z domem stoj??. One powiedzia??y, wszystko dobrze",
            0,
            True,
            5,
            1,
            excluded_nlps=["core_news_md", "core_news_sm"],
        )

    def test_potential_pair_non_personal_subject_personal_verb_noun_not_recognised(
        self,
    ):
        self.compare_potential_pair(
            "M????czyzna by??. Powiedzia??, wszystko dobrze.", 0, False, 3, 1
        )

    def test_potential_pair_non_personal_subject_personal_verb_control_1(self):
        self.compare_potential_pair(
            "Piotr by??. Powiedzia??, wszystko dobrze.", 0, False, 3, 2
        )

    def test_potential_pair_non_personal_subject_personal_verb_control_2(self):
        self.compare_potential_pair(
            "Anna by??a. Powiedzia??a, wszystko dobrze.", 0, False, 3, 2
        )

    def test_potential_pair_non_personal_subject_personal_verb_control_conjunction_1(
        self,
    ):
        self.compare_potential_pair(
            "Piotr i dom byli. Powiedzieli, wszystko dobrze.", 0, True, 5, 2
        )

    def test_potential_pair_non_personal_subject_personal_verb_control_conjunction_2(
        self,
    ):
        self.compare_potential_pair(
            "Dom i Piotr byli. Powiedzieli, wszystko dobrze.", 0, True, 5, 2
        )

    def test_potential_pair_problem_sentence_1(self):
        self.compare_potential_pair(
            "M??wi?? o kryzysie polskiej rodziny dotkni??tej plag?? rozwod??w i alkoholizmem. Bywa??o, ??e krzycza??.",
            9,
            False,
            11,
            0,
        )

    def test_potential_pair_two_singular_verb_anaphors(self):
        self.compare_potential_pair(
            "Buduje i cieszy si??. On jest szcz????liwy", 0, True, 5, 2
        )

    def test_potential_pair_two_singular_verb_anaphors_control(self):
        self.compare_potential_pair(
            "Buduje i cieszy si??. Oni s?? szcz????liwi", 0, True, 5, 0
        )

    def test_potential_pair_singular_verb_anaphor_with_comitative_phrase_simple(self):
        self.compare_potential_pair(
            "Piotr by?? szcz????liwy. Kupi?? z ??on?? nowy dom.", 0, False, 4, 2
        )

    def test_potential_pair_plural_verb_anaphor_with_comitative_phrase_simple(self):
        self.compare_potential_pair(
            "Piotr by?? szcz????liwy. Kupili z ??on?? nowy dom.",
            0,
            False,
            4,
            2,
            excluded_nlps=["core_news_sm"],
        )

    def test_potential_pair_plural_verb_anaphor_with_comitative_phrase_coordination(
        self,
    ):
        self.compare_potential_pair(
            "Piotr by?? szcz????liwy. Kupili z kole??ank?? i znajom?? nowy dom.",
            0,
            False,
            4,
            2,
        )

    def test_potential_pair_plural_verb_anaphor_with_comitative_phrase_coordination_everywhere(
        self,
    ):
        self.compare_potential_pair(
            "Piotr i Janek byli szcz????liwy. Kupili z kole??ank?? i znajom?? nowy dom.",
            0,
            True,
            6,
            2,
        )

    def compare_potential_reflexive_pair(
        self,
        doc_text,
        referred_index,
        include_dependent_siblings,
        referring_index,
        expected_truth,
        expected_reflexive_truth,
        is_reflexive_anaphor_truth,
        *,
        excluded_nlps=[]
    ):
        def func(nlp):

            if nlp.meta["name"] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            assert rules_analyzer.is_independent_noun(
                doc[referred_index]
            ) or rules_analyzer.is_potential_anaphor(doc[referred_index])
            assert rules_analyzer.is_potential_anaphor(doc[referring_index])
            referred_mention = Mention(doc[referred_index], include_dependent_siblings)
            self.assertEqual(
                expected_truth,
                rules_analyzer.is_potential_anaphoric_pair(
                    referred_mention, doc[referring_index], True
                ),
                nlp.meta["name"],
            )
            self.assertEqual(
                expected_reflexive_truth,
                rules_analyzer.is_potential_reflexive_pair(
                    referred_mention, doc[referring_index]
                ),
                nlp.meta["name"],
            )
            self.assertEqual(
                is_reflexive_anaphor_truth,
                rules_analyzer.is_reflexive_anaphor(doc[referring_index]),
                nlp.meta["name"],
            )

        self.all_nlps(func)

    def test_reflexive_in_wrong_situation_different_sentence(self):
        self.compare_potential_reflexive_pair(
            "Widzia??em cz??owieka. Cz??owiek widzia?? siebie.", 1, False, 5, 0, False, 2
        )

    def test_reflexive_in_wrong_situation_different_sentence_control(self):
        self.compare_potential_reflexive_pair(
            "Widzia??em cz??owieka. Drugi cz??owiek widzia?? go.",
            1,
            False,
            6,
            2,
            False,
            0,
            excluded_nlps=["core_news_sm"],
        )

    def test_reflexive_in_wrong_situation_same_sentence_1(self):
        self.compare_potential_reflexive_pair(
            "Widzia??em cz??owieka, dop??ki drugi cz??owiek siebie widzia??.",
            1,
            False,
            6,
            0,
            False,
            2,
        )

    def test_reflexive_in_wrong_situation_same_sentence_control(self):
        self.compare_potential_reflexive_pair(
            "Widzia??em cz??owieka, dop??ki drugi cz??owiek go widzia??.",
            1,
            False,
            6,
            2,
            False,
            0,
        )

    def test_non_reflexive_in_wrong_situation_same_sentence(self):
        self.compare_potential_reflexive_pair(
            "Cz??owiek widzia?? go.",
            0,
            False,
            2,
            0,
            True,
            0,
            excluded_nlps=["core_news_sm"],
        )

    def test_non_reflexive_in_wrong_situation_same_sentence_control(self):
        self.compare_potential_reflexive_pair(
            "Cz??owiek widzia?? siebie.", 0, False, 2, 2, True, 2
        )

    def test_non_reflexive_in_wrong_situation_same_sentence_instr(self):
        self.compare_potential_reflexive_pair(
            "Cz??owiek poszed?? z nim.",
            0,
            False,
            3,
            0,
            True,
            0,
            excluded_nlps=["core_news_sm"],
        )

    def test_non_reflexive_in_wrong_situation_same_sentence_instr_control(self):
        self.compare_potential_reflexive_pair(
            "Cz??owiek poszed?? ze sob??.", 0, False, 3, 2, True, 2
        )

    def test_non_reflexive_in_same_sentence_with_verb_conjunction(self):
        self.compare_potential_reflexive_pair(
            "Cz??owiek s??ysza?? wszystko i widzia?? siebie.", 0, False, 5, 2, True, 2
        )

    def test_reflexive_in_right_situation_modal(self):
        self.compare_potential_reflexive_pair(
            "Cz??owiek chcia?? siebie wiedzie??.", 0, False, 2, 2, True, 2
        )

    def test_reflexive_in_right_situation_zu_clause(self):
        self.compare_potential_reflexive_pair(
            "Cz??owiek my??la?? o tym, by siebie wiedzie??.", 0, False, 6, 2, True, 2
        )

    def test_reflexive_in_right_situation_within_subordinate_clause(self):
        self.compare_potential_reflexive_pair(
            "Wiedzia??, ??e cz??owiek widzia?? siebie.", 3, False, 5, 2, True, 2
        )

    def test_reflexive_in_right_situation_within_subordinate_clause_control(self):
        self.compare_potential_reflexive_pair(
            "Piotr wiedzia??, ??e cz??owiek widzia?? siebie.", 0, False, 6, 0, False, 2
        )

    def test_reflexive_in_right_situation_within_subordinate_clause_anaphor_first(self):
        self.compare_potential_reflexive_pair(
            "Piotr wiedzia??, ??e sobie cz??owiek dom budowa??.", 5, False, 4, 2, True, 2
        )

    def test_reflexive_in_right_situation_within_subordinate_clause_anaphor_first_control(
        self,
    ):
        self.compare_potential_reflexive_pair(
            "Piotr wiedzia??, ??e sobie cz??owiek dom budowa??.", 0, False, 4, 0, False, 2
        )

    def test_reflexive_with_conjuction(self):
        self.compare_potential_reflexive_pair(
            "Dom i samoch??d przewy??sza??y siebie", 0, True, 4, 2, True, 2
        )

    def test_reflexive_with_passive(self):
        self.compare_potential_reflexive_pair(
            "Dom by?? przewy??szany przez siebie", 0, False, 4, 2, True, 2
        )

    def test_reflexive_with_passive_and_conjunction(self):
        self.compare_potential_reflexive_pair(
            "Dom i samoch??d by??y przewy??szane przez siebie", 0, True, 6, 2, True, 2
        )

    def test_reflexive_with_object_antecedent(self):
        self.compare_potential_reflexive_pair(
            "Ch??opiec przemieszcza?? substancje ze sob??.", 2, False, 4, 2, True, 2
        )
        self.compare_potential_reflexive_pair(
            "Ch??opiec przemieszcza?? substancje ze sob??.", 0, False, 4, 2, True, 2
        )

    @unittest.skipIf(train_version_mismatch, train_version_mismatch_message)
    def test_reflexive_with_object_antecedent_and_coordination(self):
        self.compare_potential_reflexive_pair(
            "Ch??opiec przemieszcza?? substancje i s??l ze sob??.", 2, True, 6, 2, True, 2
        )
        self.compare_potential_reflexive_pair(
            "Ch??opiec przemieszcza?? substancje i s??l ze sob??.", 0, False, 6, 2, True, 2
        )

    def test_reflexive_with_object_antecedent_control_preceding(self):
        self.compare_potential_reflexive_pair(
            "Ch??opiec przemieszcza?? ze sob?? substancje.", 4, False, 3, 0, False, 2
        )
        self.compare_potential_reflexive_pair(
            "Ch??opiec przemieszcza?? ze sob?? substancje.", 0, False, 3, 2, True, 2
        )

    def test_reflexive_with_verb_coordination_one_subject(self):
        self.compare_potential_reflexive_pair(
            "On to zobaczy?? i pogratulowa?? siebie.", 0, False, 5, 2, True, 2
        )

    def test_reflexive_with_verb_coordination_two_subjects(self):
        self.compare_potential_reflexive_pair(
            "On to zobaczy?? i jego szef pogratulowa?? siebie.", 0, False, 7, 0, False, 2
        )

    def test_reflexive_with_to(self):
        self.compare_potential_reflexive_pair(
            "Chcieli, ??eby siebie ch??opiec zna??", 4, False, 3, 2, True, 2
        )

    def test_non_reflexive_in_wrong_situation_subordinate_clause(self):
        self.compare_potential_reflexive_pair(
            "Pomimo, ??e go zobaczy??, by?? szcz????liwy", 4, False, 3, 0, True, 0
        )

    def test_reflexive_completely_within_noun_phrase_1(self):
        self.compare_potential_reflexive_pair(
            "Opinia mojego przyjaciela o sobie by??a przesadna",
            2,
            False,
            4,
            2,
            True,
            2,
        )

    def test_reflexive_completely_within_noun_phrase_1_control(self):
        self.compare_potential_reflexive_pair(
            "Opinia mojego przyjaciela o nim by??a przesadna",
            2,
            False,
            4,
            0,
            True,
            0,
            excluded_nlps=["core_news_md"],
        )

    def test_reflexive_double_coordination_without_preposition(self):
        self.compare_potential_reflexive_pair(
            "Piotr i Agnieszka widzieli jego i j??", 0, False, 4, 0, True, 0
        )
        self.compare_potential_reflexive_pair(
            "Piotr i Agnieszka widzieli jego i j??",
            2,
            False,
            6,
            0,
            True,
            False,
            excluded_nlps=["core_news_md", "core_news_sm"],
        )

    def test_reflexive_double_coordination_with_preposition(self):
        self.compare_potential_reflexive_pair(
            "Piotr i Agnieszka rozmawiali z nim i z ni??", 0, False, 5, 0, True, 0
        )
        self.compare_potential_reflexive_pair(
            "Piotr i Agnieszka rozmawiali z nim i z ni??",
            2,
            False,
            8,
            0,
            True,
            False,
            excluded_nlps=["core_news_md", "core_news_sm"],
        )

    def test_reflexive_posessive_same_noun_phrase(self):
        self.compare_potential_reflexive_pair(
            "By?? zaj??ty swoj?? prac??", 3, False, 2, 0, False, 2
        )

    def test_reflexive_with_cataphora_control(self):
        self.compare_potential_reflexive_pair(
            "Poniewa?? by?? zaj??ty swoj?? prac??, Janek mia?? jej do????.",
            4,
            False,
            3,
            0,
            False,
            2,
        )

    def test_reflexive_with_non_reflexive_possessive_pronoun(self):
        self.compare_potential_reflexive_pair(
            "Janek zjad?? jego kolacj??.", 0, False, 2, 2, True, 1
        )

    def test_reflexive_relative_clause_subject(self):
        self.compare_potential_reflexive_pair(
            "M????czyzna, kt??ry go widzia??, przyjecha?? do domu.", 0, False, 3, 0, True, 0
        )

    def test_reflexive_relative_clause_object(self):
        self.compare_potential_reflexive_pair(
            "M????czyzna, kt??rego widzia??, przyjecha?? do domu.", 0, False, 3, 0, True, 0
        )

    def test_reflexive_relative_clause_subject_with_conjunction(self):
        self.compare_potential_reflexive_pair(
            "M????czyzna i kobieta, kt??rzy ich widzieli, przyjechali do domu.",
            0,
            True,
            5,
            0,
            True,
            0,
            excluded_nlps=["core_news_sm"],
        )

    def test_reflexive_relative_clause_object_with_conjunction(self):
        self.compare_potential_reflexive_pair(
            "M????czyzna i kobieta, kt??rych widzieli, przyjechali do domu.",
            0,
            True,
            5,
            0,
            True,
            0,
            excluded_nlps=["core_news_md"],
        )

    def compare_potentially_introducing(
        self, doc_text, index, expected_truth, *, excluded_nlps=[]
    ):
        def func(nlp):

            if nlp.meta["name"] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            self.assertEqual(
                expected_truth,
                rules_analyzer.is_potentially_introducing_noun(doc[index]),
                nlp.meta["name"],
            )

        self.all_nlps(func)

    def test_potentially_introducing_with_preposition(self):
        self.compare_potentially_introducing("On mieszka r??wnie?? z facetem", 4, True)

    @unittest.skipIf(train_version_mismatch, train_version_mismatch_message)
    def test_potentially_introducing_with_ten_control(self):
        self.compare_potentially_introducing(
            "On mieszka z tym koleg??",
            4,
            False,
            excluded_nlps=["core_news_md", "core_news_sm"],
        )

    def test_potentially_introducing_with_ten_and_relative_clause(self):
        self.compare_potentially_introducing(
            "On mieszka z tym koleg??, kt??rego znasz",
            4,
            True,
            excluded_nlps=["core_news_sm"],
        )

    def compare_potentially_referring_back_noun(
        self, doc_text, index, expected_truth, *, excluded_nlps=[]
    ):
        def func(nlp):

            if nlp.meta["name"] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            self.assertEqual(
                expected_truth,
                rules_analyzer.is_potentially_referring_back_noun(doc[index]),
                nlp.meta["name"],
            )

        self.all_nlps(func)

    def test_potentially_referring_back_noun_with_ten(self):
        self.compare_potentially_referring_back_noun(
            "Mieszka z tym koleg??",
            3,
            True,
            excluded_nlps=["core_news_md", "core_news_sm"],
        )

    def test_potentially_referring_back_noun_with_ten_and_relative_clause_control(self):
        self.compare_potentially_referring_back_noun(
            "Mieszka z tym koleg??, kt??rego znasz",
            3,
            False,
            excluded_nlps=["core_news_md"],
        )

    def test_get_dependent_sibling_info_apposition_control(self):
        self.compare_get_dependent_sibling_info(
            "Richard, wielki informatyk, poszed?? do domu", 0, "[]", None, False
        )

    def test_get_governing_sibling_info_apposition_control(self):
        self.compare_get_dependent_sibling_info(
            "Richard, wielki informatyk, poszed?? do domu", 3, "[]", None, False
        )
