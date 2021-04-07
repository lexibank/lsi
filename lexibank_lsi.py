from pathlib import Path
import unicodedata

import attr
from pylexibank import Concept, Language, FormSpec
from pylexibank.dataset import Dataset as BaseDataset
from pylexibank import progressbar

from lingpy import *
from clldutils.misc import slug


@attr.s
class CustomConcept(Concept):
    PageNumber = attr.ib(default=None)


@attr.s
class CustomLanguage(Language):
    NameInSource = attr.ib(default=None)
    NumberInSource = attr.ib(default=None)
    Order = attr.ib(default=None)
    FamilyInSource = attr.ib(default=None)
    SubGroup = attr.ib(default=None)


class Dataset(BaseDataset):
    id = "lsi"
    dir = Path(__file__).parent
    concept_class = CustomConcept
    language_class = CustomLanguage
    form_spec = FormSpec(
        separators=";,~/",
        brackets={"(": ")", "[": "]"},
        missing_data=(
            "-",
            "?",
            "...",
            "-",
            '…'
        ),
        first_form_only=True,
        strip_inside_brackets=True)

    def cmd_makecldf(self, args):
        args.writer.add_sources()

        # add concepts from list
        concepts = {}
        for concept in self.conceptlists[0].concepts.values():
            cid = '{0}_{1}'.format(concept.number, slug(concept.english))
            args.writer.add_concept(
                ID=cid,
                PageNumber=concept.attributes['pagenumber'],
                Name=concept.english,
                Concepticon_ID=concept.concepticon_id,
                Concepticon_Gloss=concept.concepticon_gloss,
            )
            concepts[concept.attributes['pagenumber']+' '+concept.english] = cid

        languages = args.writer.add_languages(
            id_factory=lambda l: slug(l['Name'], lowercase=False),
            lookup_factory=lambda l: slug(l['NameInSource']))

        D = {0: ['doculect', 'concept', 'number', 'form']}
        idx = 1

        for f in sorted(self.raw_dir.glob('LSI_txt/*/*.txt')):
            current_language = ''
            concept = f.name[:-4]
            for line in f.read_text(encoding='utf8').splitlines():
                line = unicodedata.normalize('NFD', line)
                if line.strip().startswith('NOTE'):
                    continue
                cells = line.split('\t')
                if len(cells) != 3:
                    continue
                number, language, form = cells
                if not language.strip():
                    language = current_language
                else:
                    current_language = language
                if number[:4] == "546.":
                    language = "Bengali, Eastern"
                if language.strip():
                    D[idx] = [language, concept, number, form]
                    idx += 1
        wl = Wordlist(D)
        wl.output('tsv', prettify=False, filename=str(self.raw_dir.joinpath('wordlist')))

        missingc, missingl = set(), set()
        for idx, doculect, concept, number, form in progressbar(wl.iter_rows(
                'doculect', 'concept', 'number', 'form'), desc='cldfify'):
            if concept in concepts and slug(doculect) in languages:
                args.writer.add_forms_from_value(
                    Value=form,
                    Parameter_ID=concepts[concept],
                    Language_ID=languages[slug(doculect)]
                )
            else:
                if concept not in concepts:
                    missingc.add(concept)
                if slug(doculect) not in languages:
                    missingl.add(slug(doculect))
        for m in missingc:
            print(m)
        print('')
        for m in missingl:
            print(m)
