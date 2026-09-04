# -*- coding: utf-8 -*-
"""Generator strony sterowany treścią z content/*.yml.
Netlify uruchamia ten skrypt przy każdej zmianie w panelu i publikuje wynik z ./public.
Body sekcji pochodzą z pliku źródłowego (source.html); edytowalne pola z content/site.yml."""
import os, re, yaml, shutil
from bs4 import BeautifulSoup

HERE=os.path.dirname(os.path.abspath(__file__))
DOMAIN="https://fotokaz.pl"
SRC=os.path.join(HERE,"source.html")            # kopia jednoplikowej wersji (źródło układu)
OUT=os.path.join(HERE,"public")
site=yaml.safe_load(open(os.path.join(HERE,"content","site.yml"),encoding="utf-8"))
pages_cfg=yaml.safe_load(open(os.path.join(HERE,"content","pages.yml"),encoding="utf-8"))

soup=BeautifulSoup(open(SRC,encoding="utf-8").read(),"html.parser")

# ---- style.css ----
css=soup.find("style").text+"\n.ppage{display:block}\n"

NAV=[("kulinarna.html","Kulinarna","Food"),("biznes.html","Biznes","Business"),
     ("hotele.html","Hotele","Hotels"),
     ("wydarzenia.html","Wydarzenia","Events"),("teatr.html","Teatr","Theatre"),
     ("sluby.html","Śluby","Weddings"),("wyroznienia.html","Wyróżnienia","Awards"),
     ("o-mnie.html","O mnie","About"),("kontakt.html","Kontakt","Contact")]

def esc(s): return s.replace("&","&amp;").replace('"',"&quot;")

def transform(inner_html, lang):
    frag=BeautifulSoup(inner_html,"html.parser")
    for node in frag.find_all(attrs={"data-en":True}):
        en=node.get("data-en")
        if lang=="en":
            node.clear()
            for c in list(BeautifulSoup(en,"html.parser").contents): node.append(c)
        del node["data-en"]
        if node.has_attr("data-pl"): del node["data-pl"]
    return frag.decode_contents()

# ---- edytowalne pola: (id -> {pl_anchor, en_anchor}) ----
# anchor to obecny tekst w źródle; podmieniamy go na wartość z content/site.yml
ANCHORS={
 "reviews_badge":(
   "<b>5,0 / 5</b> · 133 opinie na Google, 309 na Facebooku",
   "<b>5.0 / 5</b> · 133 reviews on Google, 309 on Facebook"),
 "review1_quote":(
   "Zdjęcia pełne emocji, ciepła i pozytywnej energii. Kadry nietuzinkowe, naturalne, wzruszające. Prosto z aparatu wyglądają idealnie. Czuliśmy się, jakbyśmy znali się od lat.",
   "Photos full of emotion, warmth and positive energy. Unconventional, natural, moving frames. Straight out of camera they look perfect. We felt like we had known him for years."),
 "review2_quote":(
   "Naturalne, piękne, oddające emocje, a przy tym oryginalne. Zaufajcie Marcinowi, a nie będziecie żałować. Zadzieje się magia. Szkoda, że nie można dać dziesiątki.",
   "Natural, beautiful, full of emotion and at the same time original. Trust Marcin and you will not regret it. Magic will happen. A shame you cannot give a 10."),
 "review3_quote":(
   "Świetnie wyłapuje emocje. Jego pomysły sprawiają, że zapominasz, że jesteś przed obiektywem. My i goście weselni jesteśmy zachwyceni zdjęciami.",
   "He catches emotion brilliantly. His ideas make you forget you are in front of the lens. We and our wedding guests are delighted with the photos."),
 "cap_kulinarna":(
   "Zdjęcie, które sprzedaje danie, zanim gość spojrzy w menu. Ustawiam światło, czekam na ten moment i łapię teksturę, parę, ociekający sos… tak, żeby ślinka ciekła. Każde danie ma swój charakter i pod to buduję kadr, nie pod cudzy szablon.",
   "A photo that sells the dish before the guest even opens the menu. I set the light, wait for the moment and catch the texture, the steam, the dripping sauce… so your mouth waters. Every dish has its own character and I build the frame around it, not around a template."),
 "cap_biznes":(
   "Wnętrza, portrety i marki pokazane tak, jak chcecie być zapamiętani. Każde miejsce ma swoją duszę, moją robotą jest ją wyłapać i sprawić, żeby budowała zaufanie od pierwszego spojrzenia.",
   "Interiors, portraits and brands shown the way you want to be remembered. Every place has its own soul, and my job is to catch it and make it build trust from the first glance."),
 "cap_wydarzenia":(
   "Scena, kulisy, twarze gwiazd i szał tłumu. Łapię ten jeden moment, którego nie da się powtórzyć… i oddaję energię tak, żebyście poczuli, że tam byliście.",
   "Stage, backstage, the faces of the stars and the roar of the crowd. I catch the one moment that cannot be repeated… and carry the energy so you feel like you were there."),
 "cap_teatr":(
   "To, co dzieje się między próbą a premierą, czego widz nigdy nie zobaczy. Fotografuję teatr tak, jak go czuję… światło, gest, napięcie tuż przed tym, aż aktor przestaje grać, a zaczyna być.",
   "What happens between rehearsal and opening night, what the audience never sees. I photograph theatre the way I feel it… light, gesture, the tension right before the actor stops acting and starts being."),
 "cap_hotele":(
   'Hotel to obietnica, a wnętrze ją składa. Fotografuję przestrzenie tak, żeby światło, faktura i klimat sprzedawały pobyt, zanim gość przekroczy próg.',
   'A hotel is a promise and the interior keeps it. I photograph spaces so that light, texture and atmosphere sell the stay before the guest even walks in.'),
 "cap_sluby":(
   "Wasz dzień opowiedziany po swojemu, od pierwszych nerwów przy makijażu po ostatni taniec. Nie ustawiam scenek, czekam na to, co dzieje się samo… żebyście za lata przeżyli ten dzień jeszcze raz, patrząc na zdjęcia.",
   "Your day told your way, from the first nerves at the makeup chair to the last dance. I do not stage little scenes, I wait for what happens on its own… so that years later you relive that day again, looking at the photos."),
}

def apply_content(html, lang):
    idx=0 if lang=="pl" else 1
    for fid,(pl,en) in ANCHORS.items():
        anchor=(pl,en)[idx]
        val=site.get(fid,{}).get(lang)
        if val is None: continue
        if anchor in html:
            html=html.replace(anchor, val)
    return html

def nav_html(cur,lang):
    logo='<a href="index.html" class="logo" aria-label="Marcin Kaźmieruk Fotografia — strona główna">foto<span>kaz</span></a>'
    items=""
    for f,pl,en in NAV:
        act=' class="active"' if f==cur else ''
        items+=f'<a href="{f}"{act}>{en if lang=="en" else pl}</a>'
    lang_link=(f'<a href="../{cur}" class="lang" hreflang="pl">PL</a>' if lang=="en"
               else f'<a href="en/{cur}" class="lang" hreflang="en">EN</a>')
    return f'<nav>\n  {logo}\n  <div class="links">{items}{lang_link}</div>\n  <button class="menu-btn" aria-label="Menu">&#9776;</button>\n</nav>'

def footer_html(lang):
    if lang=="en":
        tag="Marcin Kaźmieruk · Food, business, event, theatre and wedding photography"; priv="Privacy policy"
        copy="ELT-Centre Marcin Kaźmieruk · NIP 6112505234 · © 2026. All rights reserved."; lab={f:en for f,pl,en in NAV}
    else:
        tag="Marcin Kaźmieruk · Fotografia kulinarna · biznesowa · eventowa · teatralna · ślubna"; priv="Polityka prywatności"
        copy="ELT-Centre Marcin Kaźmieruk · NIP 6112505234 · © 2026. Wszystkie prawa zastrzeżone."; lab={f:pl for f,pl,en in NAV}
    fn="".join(f'<a href="{f}">{lab[f]}</a>' for f,_,_ in NAV)
    return f'<footer><div class="wrap">\n  <div class="logo">foto<span>kaz</span></div>\n  <div class="tag">{tag}</div>\n  <div class="fnav">{fn}</div>\n  <div class="fnav" style="margin-top:4px"><a href="prywatnosc.html">{priv}</a></div>\n  <div class="copy">{copy}</div>\n</div></footer>'

SCRIPT=open(os.path.join(HERE,"_script.html"),encoding="utf-8").read()

def jsonld(page,lang):
    b=DOMAIN
    biz='{"@context":"https://schema.org","@type":"LocalBusiness","name":"Marcin Kaźmieruk Fotografia","image":"%s/images/sluby/12.jpg","@id":"%s/#business","url":"%s/","telephone":"+48505183969","email":"m_kazmieruk@10g.pl","address":{"@type":"PostalAddress","streetAddress":"ul. Podgórze 1A/1","addressLocality":"Jelenia Góra","postalCode":"58-500","addressRegion":"Dolny Śląsk","addressCountry":"PL"},"areaServed":["PL","Europe"],"priceRange":"$$$","sameAs":["https://www.facebook.com/marcin4funphotos","https://www.instagram.com/marcin4funphotos","https://www.instagram.com/fotofoodie"],"aggregateRating":{"@type":"AggregateRating","ratingValue":"5.0","reviewCount":"133","bestRating":"5"},"founder":{"@type":"Person","name":"Marcin Kaźmieruk","jobTitle":"Fotograf","award":["#1 Foodelia 2025","IPA 2026","Flash Masters Top 10","Two Mann Studios Scholarship","Osobowość Roku 2025 Jelenia Góra"]},"knowsAbout":["fotografia kulinarna","fotografia komercyjna","fotografia eventowa","fotografia ślubna","fotografia teatralna"]}'%(b,b,b)
    out=[biz]
    if page=="o-mnie.html":
        out.append('{"@context":"https://schema.org","@type":"Person","name":"Marcin Kaźmieruk","jobTitle":"Fotograf","url":"%s/o-mnie.html","knowsLanguage":["pl","en"]}'%b)
    return "\n".join('<script type="application/ld+json">%s</script>'%o for o in out)

def build(page,lang):
    cfg=pages_cfg[page]
    title=cfg["title_"+lang]; desc=cfg["desc_"+lang]
    ppage=soup.find("div",attrs={"data-page":page})
    inner=transform(ppage.decode_contents(),lang)
    inner=apply_content(inner,lang)
    if lang=="en":
        inner=re.sub(r'(src|href)="images/', r'\1="../images/', inner)
        cssref="../style.css"; canon=(f"{DOMAIN}/en/" if page=="index.html" else f"{DOMAIN}/en/{page}"); loc="en_GB"; hl="en"
        alt_pl=(f"{DOMAIN}/" if page=="index.html" else f"{DOMAIN}/{page}"); alt_en=canon
    else:
        cssref="style.css"; canon=(f"{DOMAIN}/" if page=="index.html" else f"{DOMAIN}/{page}"); loc="pl_PL"; hl="pl"
        alt_pl=canon; alt_en=(f"{DOMAIN}/en/" if page=="index.html" else f"{DOMAIN}/en/{page}")
    ogimg=f"{DOMAIN}/images/food/51.jpg"
    robots='<meta name="robots" content="noindex,follow">' if cfg.get("noindex") else '<meta name="robots" content="index,follow,max-image-preview:large">'
    doc=f'''<!DOCTYPE html>
<html lang="{hl}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{robots}
<link rel="canonical" href="{canon}">
<link rel="alternate" hreflang="pl" href="{alt_pl}">
<link rel="alternate" hreflang="en" href="{alt_en}">
<link rel="alternate" hreflang="x-default" href="{alt_pl}">
<meta name="author" content="Marcin Kaźmieruk">
<meta name="theme-color" content="#0a0e1a">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Marcin Kaźmieruk Fotografia">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{ogimg}">
<meta property="og:locale" content="{loc}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..700&family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{cssref}">
{jsonld(page,lang)}
</head>
<body>
<a href="#main" class="skip-link">{'Skip to content' if lang=='en' else 'Przejdź do treści'}</a>
{nav_html(page,lang)}
<main id="main"><div class="ppage show">
{inner}
</div></main>
{footer_html(lang)}
{SCRIPT}
</body>
</html>'''
    return doc

# ---- write ----
os.makedirs(os.path.join(OUT,"en"),exist_ok=True)
open(os.path.join(OUT,"style.css"),"w",encoding="utf-8").write(css)
for page in pages_cfg:
    open(os.path.join(OUT,page),"w",encoding="utf-8").write(build(page,"pl"))
    open(os.path.join(OUT,"en",page),"w",encoding="utf-8").write(build(page,"en"))
# sitemap + robots
urls=[]
for page in pages_cfg:
    for pref in ("","en/"):
        loc=(f"{DOMAIN}/{pref}" if page=="index.html" else f"{DOMAIN}/{pref}{page}")
        pr="1.0" if page=="index.html" else ("0.5" if pages_cfg[page].get("noindex") else "0.8")
        urls.append(f"  <url><loc>{loc}</loc><changefreq>monthly</changefreq><priority>{pr}</priority></url>")
open(os.path.join(OUT,"sitemap.xml"),"w",encoding="utf-8").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+"\n".join(urls)+"\n</urlset>\n")
open(os.path.join(OUT,"robots.txt"),"w",encoding="utf-8").write(f"User-agent: *\nAllow: /\nDisallow: /prywatnosc.html\nDisallow: /en/prywatnosc.html\nDisallow: /admin/\n\nSitemap: {DOMAIN}/sitemap.xml\n")
# skopiuj zdjęcia i panel do public/
for d in ("images","admin"):
    s=os.path.join(HERE,d)
    if os.path.isdir(s):
        shutil.copytree(s, os.path.join(OUT,d), dirs_exist_ok=True)
print("OK build ->", OUT)
