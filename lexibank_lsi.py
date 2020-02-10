from collections import OrderedDict, defaultdict

import attr
from pathlib import Path
from pylexibank import Concept, Language
from pylexibank.dataset import Dataset as BaseDataset
from pylexibank.util import pb

from lingpy import *
from clldutils.misc import slug

#@attr.s
#class CustomConcept(Concept):
#    Chinese_Gloss = attr.ib(default=None)


#@attr.s
#class CustomLanguage(Language):


class Dataset(BaseDataset):
    id = "lsi"
    dir = Path(__file__).parent
    #concept_class = CustomConcept
    #language_class = CustomLanguage

    def cmd_makecldf(self, args):

        files = sorted(self.raw_dir.glob('LSI_txt/*/*.txt'))

        D = {
                0: ['doculect', 'concept', 'number', 'form']
                }
        idx = 1
        current_language = ''
        for f in files:
            concept = f.name[:-4]
            args.log.info('Parsing {0}'.format(concept))
            with open(f) as this_file:
                data = this_file.readlines()
                for line in data:
                    if line.startswith('NOTE'):
                        continue
                    cells = line.strip('\n').split('\t')
                    if len(cells) != 3:
                        continue
                    number, language, form = cells
                    if not language.strip():
                        language = current_language
                    else:
                        current_language = language
                    D[idx] = [language, concept, number, form]
                    idx += 1
        wl = Wordlist(D)
        wl.output(
                'tsv',
                prettify=False,
                filename=self.raw_dir.joinpath('wordlist').as_posix()
                )


