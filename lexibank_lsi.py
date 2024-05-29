import shutil
import pathlib
import unicodedata

import attr
from csvw.metadata import URITemplate
from csvw.dsv import UnicodeWriter
from pylexibank import Concept, Language, FormSpec
from pylexibank.dataset import Dataset as BaseDataset
from pylexibank import progressbar
import pycldf
from pycldf.media import File
from clldutils.jsonlib import dump, load

from lingpy import *
from clldutils.misc import slug

DSAL_BASE_URL = 'https://dsal.uchicago.edu/books/lsi/'


@attr.s
class CustomConcept(Concept):
    DSAL_URL = attr.ib(default=None)
    PageNumber = attr.ib(
        default=None,
        metadata={"dc:description": "Range of pages in the printed survey"}
    )
    Scans = attr.ib(
        default=None,
        metadata={
            'separator': ' ',
            'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#mediaReference',
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
    dir = pathlib.Path(__file__).parent
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

    def cmd_download(self, args):
        cols = ['NAME', 'FAMCODE', 'SUBGRPCD', 'LANGCODE', 'DIALCODE']
        with UnicodeWriter(self.etc_dir / 'geolangs.csv') as w:
            w.writerow(['dir'] + cols + ['Glottocode', 'LSI_ID'])
            for p in self.raw_dir.joinpath('geo').glob('*/features.geojson'):
                rows = set()
                for f in load(p)['features']:
                    if 'Polygon' in f['geometry']['type'] and f['properties']['NAME']:
                        rows.add(tuple(f['properties'].get(col, '') for col in cols))
                for row in sorted(rows):
                    w.writerow([p.parent.name] + list(row) + ['', ''])
        return
        # copy ll-map images over here
        llmap = pycldf.Dataset.from_metadata(
            self.raw_dir / 'LL-MAP' / 'cldf' / 'Generic-metadata.json')
        for contrib in llmap.objects('ContributionTable'):
            if contrib.cldf.name.startswith('Linguistic Survey of India'):
                d = None
                for f in contrib.all_related('mediaReference'):
                    if not f.cldf.pathInZip:
                        p = pathlib.Path(f.cldf.downloadUrl.path)
                        d = self.raw_dir / 'geo' / p.stem
                        if not d.exists():
                            d.mkdir()
                        shutil.copy(p, d / p.name)
                        for name in ['{}.points'.format(p.name), '{}_modified.tif'.format(p.stem)]:
                            if p.parent.joinpath(name).exists():
                                shutil.copy(p.parent / name, d / name)
                        break
                assert d
                features = []
                for f in contrib.all_related('mediaReference'):
                    if f.cldf.pathInZip:
                        features.extend(File.from_dataset(llmap, f).read_json()['features'])
                if features:
                    dump(dict(type='FeatureCollection', features=features),
                         d / 'features.geojson',
                         indent=2)

    def cmd_makecldf(self, args):
        t = args.writer.cldf.add_component(
            'MediaTable',
            {
                'name': 'Source',
                'separator': ';',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source',
            }
        )
        t.common_props['dc:description'] = 'Scans in the Digital South Asia Library'
        args.writer.cldf['FormTable', 'Profile'].valueUrl = URITemplate(
            '../etc/orthography/{Profile}.tsv')
        args.writer.cldf['FormTable', 'Profile'].common_props['dc:description'] = \
            "Orthography profile according to Moran & Cysouw 2018 used to segment this form"
        args.writer.add_sources()

        def scan_number(s, pad=True):
            res = str(int(s) + 42)
            return res.rjust(3, '0') if pad else res

        # add concepts from list
        concepts = {}
        for concept in self.conceptlists[0].concepts.values():
            cid = '{0}_{1}'.format(concept.number, slug(concept.english))

            firstscan = None
            for i, pnumber in enumerate(concept.attributes['pagenumber'].split('-')):
                if i == 0:
                    firstscan = scan_number(pnumber, pad=False)
                snumber = scan_number(pnumber)
                args.writer.objects['MediaTable'].append(dict(
                    ID=snumber,
                    Name=pnumber,
                    Description='Scan of page {} of Vol. 1, Pt. 2'.format(pnumber),
                    Media_Type='image/jpeg',
                    Download_URL='{}images/lsi-v1-2-{}.jpg'.format(DSAL_BASE_URL, snumber),
                    Source=['LSIatDSAL'],
                ))

            args.writer.add_concept(
                ID=cid,
                DSAL_URL='{}lsi.php?volume=1-2&pages=381#page/{}/mode/2up'.format(
                    DSAL_BASE_URL, firstscan),
                PageNumber=concept.attributes['pagenumber'],
                Scans=map(scan_number, concept.attributes['pagenumber'].split('-')),
                Name=concept.english,
                Concepticon_ID=concept.concepticon_id,
                Concepticon_Gloss=concept.concepticon_gloss,
            )
            concepts[concept.attributes['pagenumber'] + ' ' + concept.english] = cid

        languages = args.writer.add_languages(
            id_factory=lambda l: slug(l['Name'], lowercase=False),
            lookup_factory=lambda l: slug(l['NameInSource']))
        for l in args.writer.objects['LanguageTable']:
            if l['Latitude'] is None and l['Glottocode']:
                glang = args.glottolog.api.get_language(l['Glottocode'])
                if glang:
                    l['Latitude'] = glang.latitude
                    l['Longitude'] = glang.longitude

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
        for idx, doculect, concept, number, form in progressbar(wl.iter_rows(
                'doculect', 'concept', 'number', 'form'), desc='cldfify'):
            args.writer.add_forms_from_value(
                Value=form,
                Parameter_ID=concepts[concept],
                Language_ID=languages[slug(doculect)],
                Source=['Grierson1928'],
            )
