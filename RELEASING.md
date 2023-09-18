# Releasing LSI

```shell
cldfbench lexibank.makecldf lexibank_lsi.py --glottolog-version v4.8 --concepticon-version v3.1.0 --clts-version v2.2.0
pytest
```

```shell
cldfbench cldfreadme lexibank_lsi.py
```

```shell
cldfbench cldfviz.map cldf --format svg --width 20 --output map.svg --with-ocean --no-legend
cldferd --format compact.svg cldf > erd.svg
```