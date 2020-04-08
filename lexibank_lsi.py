from collections import OrderedDict, defaultdict

import attr
from pathlib import Path
from pylexibank import Concept, Language, FormSpec
from pylexibank.dataset import Dataset as BaseDataset
from pylexibank import progressbar
import unicodedata

from lingpy import *
from clldutils.misc import slug

@attr.s
class CustomConcept(Concept):
    PageNumber = attr.ib(default=None)


@attr.s
class CustomLanguage(Language):
    NameInSource = attr.ib(default=None)
    


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

        files = sorted(self.raw_dir.glob('LSI_txt/*/*.txt'))
        args.writer.add_sources()

        # add concepts from list
        concepts = {}
        for concept in self.concepts:
            cid = '{0}_{1}'.format(
                    concept['NUMBER'],
                    slug(concept['ENGLISH']))
            args.log.info('adding {0}'.format(cid))
            args.writer.add_concept(
                    ID=cid,
                    PageNumber=concept['PAGENUMBER'],
                    Name=concept['ENGLISH'])
            concepts[concept['PAGENUMBER']+' '+concept['ENGLISH']] = cid

        # add languages from list
        languages = {}
        for language in progressbar(self.languages, desc='add languages'):
            args.writer.add_language(
                    ID=slug(language['Name'], lowercase=False),
                    Name=language['Name'],
                    Glottocode=language['Glottocode'],
                    NameInSource=language['NameInSource'])
            languages[slug(language['NameInSource'])] = slug(language['Name'],
                    lowercase=False)

        D = {
                0: ['doculect', 'concept', 'number', 'form']
                }
        idx = 1

        for f in files:
            current_language = ''
            concept = f.name[:-4]
            args.log.info('Parsing {0}'.format(concept))
            with open(f) as this_file:
                data = this_file.readlines()
                for line in data:
                    line = unicodedata.normalize('NFD', line) 
                    if line.strip().startswith('NOTE'):
                        continue
                    cells = line.strip('\n').split('\t')
                    if len(cells) != 3:
                        continue
                    number, language, form = cells
                    if not language.strip():
                        language = current_language
                    else:
                        current_language = language
                    if language.strip():
                        D[idx] = [language, concept, number, form]
                        idx += 1
        wl = Wordlist(D)
        wl.output(
                'tsv',
                prettify=False,
                filename=self.raw_dir.joinpath('wordlist').as_posix()
                )

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


