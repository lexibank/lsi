from lingpy import *
from lexibank_lsi import Dataset

import sys, csv
from collections import defaultdict

import random

random.seed(1234)

mylist = [x.strip("\n") for x in open("raw/concepts_2_compare.txt")]

ds = Dataset("lsi")
wl = Wordlist.from_cldf(str(ds.cldf_specs().metadata_path))

myfamilies = ["Dravidian", "Sino-Tibetan", "Indo-European", "Austroasiatic"]
families = defaultdict(list)


reader = csv.DictReader(open("cldf/languages.csv", "r"))
for row in reader:
    if row['Family'] in myfamilies:
        families[row['Family']].append(row['Name'])

    
for family in myfamilies:
    D = {0: wl.columns}
    for idx in wl:
        if wl[idx, 'concept'] in mylist and wl[idx, 'language_name'] in families[family]:
            D[idx] = wl[idx]

    wlnew = Wordlist(D)

    wlnew.output("tsv", filename="computed"+"/"+family)

    lex = LexStat("computed"+"/"+family+".tsv")
    #lex.cluster(method='sca', threshold=0.45, ref='scaid', cluster_method='infomap')
    
    lex.get_scorer(runs=1000)
    lex.cluster(method='lexstat', cluster_method='infomap', threshold=0.55, ref='infomapid')    
    
    lex.add_entries('inferred_class', 'concept,infomapid', lambda x, y: x[y[0]]+':'+str(x[y[1]]))
    lex.output('tsv', filename="computed"+"/"+family+"_lexstat_infomap",ignore="all", prettify=False)
    lex.output('paps.nex', filename="computed"+"/"+family+"_lexstat_infomap", ref="infomapid", missing="?")

    lex = LexStat("computed"+"/"+family+"_lexstat_infomap.tsv")
    alm = Alignments(lex, ref='infomapid')
    alm.align()
    alm.output('html', filename="computed"+"/"+family+"_lexstat_infomap")

D = {0: wl.columns}
for idx in wl:
    if wl[idx, 'concept'] in mylist:
        D[idx] = wl[idx]

wlnew = Wordlist(D)

wlnew.output("tsv", filename="computed/lsi_borrowings")

lex = LexStat("computed/lsi_borrowings.tsv")
lex.cluster(method='sca', threshold=0.45, ref='scaid', cluster_method='infomap')
lex.add_entries('inferred_class', 'concept,scaid', lambda x, y: x[y[0]]+':'+str(x[y[1]]))
lex.output('tsv', filename="computed/lsi_borrowings_scaid",ignore="all", prettify=False)
lex.output('paps.nex', filename="computed/lsi_borrowings_scaid", ref="scaid", missing="?")

lex = LexStat("computed/lsi_borrowings_scaid.tsv")
alm = Alignments(lex, ref='scaid')
alm.align()
alm.output('html', filename="computed"+"/"+"lsi_borrowings_scaid")
