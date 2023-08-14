from pathlib import Path
import unicodedata

import attr
from csvw.metadata import URITemplate
from pylexibank import Concept, Language, FormSpec
from pylexibank.dataset import Dataset as BaseDataset
from pylexibank import progressbar

from lingpy import *
from clldutils.misc import slug


@attr.s
class CustomConcept(Concept):
    PageNumber = attr.ib(
        default=None,
        metadata={"dc:description": "Range of pages in the printed survey"}
    )
    ScanNumbers = attr.ib(
        default=None,
        metadata={
            'separator': ' ',
            'dc:description': "Numbers of scans in the Digital South Asia Library",
            'valueUrl': 'https://dsal.uchicago.edu/books/lsi/images/lsi-v1-2-{ScanNumbers}.jpg',
        }
    )


@attr.s
class CustomLanguage(Language):
    NameInSource = attr.ib(default=None)
    NumberInSource = attr.ib(
        default=None,
        metadata={"dc:description": "Number of the language in the General List of the printed survey"}
    )
    Order = attr.ib(
        default=None,
        metadata={"dc:description": "Position of the language on the vocabulary pages of the printed survey"}
    )
    FamilyInSource = attr.ib(
        default=None,
        metadata={"dc:description": "Classification of the language in the printed survey"}
    )
    SubGroup = attr.ib(
        default=None,
        metadata={"dc:description": "Sub-classification of the language in the printed survey"}
    )


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
        args.writer.cldf['FormTable', 'Profile'].valueUrl = URITemplate(
            '../etc/orthography/{Profile}.tsv')
        args.writer.cldf['FormTable', 'Profile'].common_props['dc:description'] = \
            "Orthography profile according to Moran & Cysouw 2018 used to segment this form"
        args.writer.add_sources()

        def scan_number(s):
            return str(int(s) + 42).rjust(3, '0')

        # add concepts from list
        concepts = {}
        for concept in self.conceptlists[0].concepts.values():
            cid = '{0}_{1}'.format(concept.number, slug(concept.english))
            args.writer.add_concept(
                ID=cid,
                PageNumber=concept.attributes['pagenumber'],
                ScanNumbers=map(scan_number, concept.attributes['pagenumber'].split('-')),
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
                if number[:4] == "546.":
                    language = "Bengali, Eastern"
                
                if not language.strip():
                    language = current_language
                else:
                    current_language = language
                if language.strip():
                    D[idx] = [language, concept, number, form]
                    idx += 1
        wl = Wordlist(D)
        wl.output('tsv', prettify=False, filename=str(self.raw_dir.joinpath('wordlist')))

        for idx, doculect, concept, number, form in progressbar(wl.iter_rows(
                'doculect', 'concept', 'number', 'form'), desc='cldfify'):
            args.writer.add_forms_from_value(
                Value=form,
                Parameter_ID=concepts[concept],
                Language_ID=languages[slug(doculect)]
            )
