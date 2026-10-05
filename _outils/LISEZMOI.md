# Outils du site (non publiés)

Le dossier `_outils` n'est pas publié : GitHub Pages passe le site par Jekyll, qui laisse de côté les dossiers dont le
nom commence par « _ ».

## `langues.py` : les pages anglaises et le référencement

Les pages du site (`index.html`, `faq/`, `skins/`, `presse/`, `licence/`, `conditions/`) sont écrites dans les deux
langues et servies à la racine, en français. **Après chaque modification d'une page**, relancer :

```
python _outils/langues.py
```

Il refait :

- dans chaque page française : son titre, sa description, l'aperçu des partages et le bloc entre les marques
  « référencement : début / fin » (adresse canonique, adresse de l'autre langue, fiche pour les moteurs de recherche :
  le logiciel avec sa version et son installeur lus dans la page, les questions de la FAQ) ;
- sa page anglaise sous `en/` (sans le texte français, en anglais d'emblée, liens vers les pages anglaises) ;
- `sitemap.xml` et `robots.txt`.

**Ne jamais modifier une page de `en/` à la main** : elle est refaite à chaque passage. Les titres et descriptions des
deux langues sont dans `PAGES`, en haut du script. Une nouvelle page du site s'y ajoute aussi.

Chaque langue a sa propre adresse : la page reste dans sa langue (jamais d'après celle du navigateur : les robots des
moteurs de recherche lisent en anglais), les boutons FR et EN mènent à l'autre adresse, un lien « ?lang=en » ou un
choix déjà fait aussi, et une pastille propose l'autre version à un navigateur dans l'autre langue.
