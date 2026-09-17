# -*- coding: utf-8 -*-
"""Generator strony sterowany treścią. Netlify uruchamia go po każdej zmianie w panelu."""
import os, re, yaml, json, shutil
from bs4 import BeautifulSoup

HERE=os.path.dirname(os.path.abspath(__file__))
DOMAIN="https://fotokaz.pl"
# Link plakietki Production Paradise — profil Marcina.
PP_LISTING_URL="https://www.productionparadise.com/member/warsaw/marcin-kazmieruk"
SRC=os.path.join(HERE,"source.html")
OUT=os.path.join(HERE,"public")
site=yaml.safe_load(open(os.path.join(HERE,"content","site.yml"),encoding="utf-8"))
pages_cfg=yaml.safe_load(open(os.path.join(HERE,"content","pages.yml"),encoding="utf-8"))
galleries=yaml.safe_load(open(os.path.join(HERE,"content","galleries.yml"),encoding="utf-8")) or {}

# ---------- Wygląd strony (globalne ustawienia z panelu) ----------
FONTS={
 "fraunces_outfit":{"head":"'Fraunces',serif","body":"'Outfit',sans-serif",
   "url":"https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..700&family=Outfit:wght@300;400;500;600&display=swap"},
 "playfair_inter":{"head":"'Playfair Display',serif","body":"'Inter',sans-serif",
   "url":"https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400;1,500;1,600&family=Inter:wght@300;400;500;600&display=swap"},
 "cormorant_jost":{"head":"'Cormorant Garamond',serif","body":"'Jost',sans-serif",
   "url":"https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Jost:wght@300;400;500;600&display=swap"},
 "space_inter":{"head":"'Space Grotesk',sans-serif","body":"'Inter',sans-serif",
   "url":"https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap"},
 "libre_source":{"head":"'Libre Baskerville',serif","body":"'Source Sans 3',sans-serif",
   "url":"https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:wght@300;400;500;600&display=swap"},
}
ACCENTS={
 "blekit":("#7da2d9","#a9c5ee"),
 "zloto":("#c9a86a","#e2c78f"),
 "terakota":("#cc7a5c","#e3a184"),
 "szalwia":("#8fae8b","#b4ccb0"),
 "grafit":("#9aa7bd","#c3cddd"),
}
SIZES={  # (fs_base, fs_copy)
 "mniejszy":("15px","16px"),
 "standard":("16px","17px"),
 "wiekszy":("17px","18px"),
}
_font=FONTS.get(str(site.get("theme_font","fraunces_outfit")),FONTS["fraunces_outfit"])
_acc=ACCENTS.get(str(site.get("theme_accent","blekit")),ACCENTS["blekit"])
_sz=SIZES.get(str(site.get("theme_text_size","standard")),SIZES["standard"])
_hw=str(site.get("theme_heading_weight","400") or "400")
FONTS_LINK=('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
 '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 f'<link href="{_font["url"]}" rel="stylesheet">')
THEME_STYLE=('<style>:root{'
 f'--font-head:{_font["head"]};--font-body:{_font["body"]};'
 f'--accent:{_acc[0]};--accent-soft:{_acc[1]};'
 f'--hw-head:{_hw};--fs-base:{_sz[0]};--fs-copy:{_sz[1]}'
 '}</style>')

soup=BeautifulSoup(open(SRC,encoding="utf-8").read(),"html.parser")
css=soup.find("style").text+"\n.ppage{display:block}\n"
import hashlib
CSS_VER=hashlib.md5(css.encode("utf-8")).hexdigest()[:8]

NAV=[("kulinarna.html","Kulinarna","Food"),("biznes.html","Biznes","Business"),
     ("hotele.html","Hotele","Hotels"),
     ("wydarzenia.html","Wydarzenia","Events"),("teatr.html","Teatr","Theatre"),
     ("sluby.html","Śluby","Weddings"),("wyroznienia.html","Wyróżnienia","Awards"),
     ("o-mnie.html","O mnie","About"),("kontakt.html","Kontakt","Contact")]
SPEC_FILES={"kulinarna.html","biznes.html","hotele.html","wydarzenia.html","teatr.html","sluby.html"}
IMG_SLOTS={
 "HERO_IMG_KULINARNA":("hero_img_kulinarna","images/food/51.webp"),
 "HERO_IMG_BIZNES":("hero_img_biznes","images/biznes/11.webp"),
 "HERO_IMG_WYDARZENIA":("hero_img_wydarzenia","images/wydarzenia/30.webp"),
 "HERO_IMG_TEATR":("hero_img_teatr","images/teatr/06.webp"),
 "HERO_IMG_SLUBY":("hero_img_sluby","images/sluby/12.webp"),
 "CAT_IMG_KULINARNA":("cat_img_kulinarna","images/food/07.webp"),
 "CAT_IMG_BIZNES":("cat_img_biznes","images/biznes/05.webp"),
 "CAT_IMG_HOTELE":("cat_img_hotele","images/hotele/05.webp"),
 "CAT_IMG_WYDARZENIA":("cat_img_wydarzenia","images/wydarzenia/12.webp"),
 "CAT_IMG_TEATR":("cat_img_teatr","images/teatr/03.webp"),
 "CAT_IMG_SLUBY":("cat_img_sluby","images/sluby/05.webp"),
}

GAL_ALT={'kulinarna':'Fotografia kulinarna','biznes':'Fotografia biznesowa i portret',
         'hotele':'Fotografia wnętrz hotelowych','wydarzenia':'Fotografia eventowa',
         'teatr':'Fotografia teatralna','sluby':'Fotografia ślubna',
         'wyroznienia':'Nagroda i wyróżnienie — Marcin Kaźmieruk'}

def esc(s): return s.replace("&","&amp;").replace('"',"&quot;")

# edytowalne teksty: id -> {pl_anchor,en_anchor} wczytane z _anchors.json + stałe
ANCHORS=json.load(open(os.path.join(HERE,"_anchors.json"),encoding="utf-8"))
# uzupełnij o pola opinii/plakietki/opisów (te same anchory co wartości domyślne w site.yml)
for k in ["reviews_badge","review1_quote","review2_quote","review3_quote",
          "cap_kulinarna","cap_biznes","cap_wydarzenia","cap_teatr","cap_sluby","cap_hotele","award_intro","award_foodelia","award_ipa","award_flashmasters","award_spotlight"]:
    ANCHORS[k]={"pl":site[k]["pl"],"en":site[k]["en"]}

def transform(inner_html, lang):
    frag=BeautifulSoup(inner_html,"html.parser")
    for node in frag.find_all(attrs={"data-en":True}):
        en=node.get("data-en")
        if lang=="en":
            node.clear()
            for c in list(BeautifulSoup(en,"html.parser").contents): node.append(c)
        del node["data-en"]
        if node.has_attr("data-pl"): del node["data-pl"]
    for node in frag.find_all(attrs={"data-en-placeholder":True}):
        en=node.get("data-en-placeholder")
        if lang=="en":
            node["placeholder"]=en
        del node["data-en-placeholder"]
    return frag.decode_contents()

def apply_content(html, lang):
    for fid,pair in ANCHORS.items():
        anchor=pair[lang]; val=site.get(fid,{}).get(lang)
        if val is None: continue
        if anchor and anchor in html:
            html=html.replace(anchor, val)
    return html

def render_gallery(cat):
    base=GAL_ALT.get(cat,cat); items=""
    for i,src in enumerate(galleries.get(cat,[]) or [],1):
        src=src.lstrip('/')
        items+=f'\n      <a class="item"><img src="{src}" alt="{esc(base)} {i} — Marcin Kaźmieruk" loading="lazy"></a>'
    return items

def nav_html(cur,lang):
    logo='<a href="index.html" class="logo" aria-label="Marcin Kaźmieruk Fotografia — strona główna">foto<span>kaz</span></a>'
    spec_items=""
    for f,pl,en in NAV:
        if f not in SPEC_FILES: continue
        act=' class="active"' if f==cur else ''
        spec_items+=f'<a href="{f}"{act}>{en if lang=="en" else pl}</a>'
    drop_active=' active' if cur in SPEC_FILES else ''
    portfolio=f'<div class="nav-drop"><button type="button" class="{drop_active.strip()}" aria-expanded="false" aria-haspopup="true">Portfolio <span class="car" aria-hidden="true">&#9662;</span></button><div class="nav-drop-menu">{spec_items}</div></div>'
    rest_items=""
    for f,pl,en in NAV:
        if f in SPEC_FILES: continue
        act=' class="active"' if f==cur else ''
        rest_items+=f'<a href="{f}"{act}>{en if lang=="en" else pl}</a>'
    lang_link=(f'<a href="../{cur}" class="lang" hreflang="pl">PL</a>' if lang=="en"
               else f'<a href="en/{cur}" class="lang" hreflang="en">EN</a>')
    return f'<nav>\n  {logo}\n  <div class="links">{portfolio}{rest_items}{lang_link}</div>\n  <button class="menu-btn" aria-label="Menu">&#9776;</button>\n</nav>'

def footer_html(lang):
    if lang=="en":
        tag="Marcin Kaźmieruk · Food, business, event, theatre and wedding photography"; priv="Privacy policy"
        copy="ELT-Centre Marcin Kaźmieruk · NIP 6112505234 · © 2026. All rights reserved."; lab={f:en for f,pl,en in NAV}
    else:
        tag="Marcin Kaźmieruk · Fotografia kulinarna · biznesowa · eventowa · teatralna · ślubna"; priv="Polityka prywatności"
        copy="ELT-Centre Marcin Kaźmieruk · NIP 6112505234 · © 2026. Wszystkie prawa zastrzeżone."; lab={f:pl for f,pl,en in NAV}
    fn="".join(f'<a href="{f}">{lab[f]}</a>' for f,_,_ in NAV)
    imgpref="../" if lang=="en" else ""
    badge_alt=("Trusted member of Production Paradise" if lang=="en" else "Zaufany członek Production Paradise")
    badge=(f'\n  <div class="pp-badge"><a href="{PP_LISTING_URL}" target="_blank" rel="noopener">'
           f'<img src="{imgpref}images/pp-trusted-member.png" alt="{badge_alt}" loading="lazy" width="180" height="45"></a></div>')
    return f'<footer><div class="wrap">\n  <div class="logo">foto<span>kaz</span></div>\n  <div class="tag">{tag}</div>\n  <div class="fnav">{fn}</div>\n  <div class="fnav" style="margin-top:4px"><a href="prywatnosc.html">{priv}</a></div>{badge}\n  <div class="copy">{copy}</div>\n</div></footer>'

SCRIPT=open(os.path.join(HERE,"_script.html"),encoding="utf-8").read()

def jsonld(page,lang,inner_html=""):
    b=DOMAIN
    biz='{"@context":"https://schema.org","@type":"LocalBusiness","name":"Marcin Kaźmieruk Fotografia","image":"%s/images/sluby/12.webp","@id":"%s/#business","url":"%s/","telephone":"+48505183969","email":"info@fotokaz.pl","address":{"@type":"PostalAddress","streetAddress":"ul. Podgórze 1A/1","addressLocality":"Jelenia Góra","postalCode":"58-500","addressRegion":"Dolny Śląsk","addressCountry":"PL"},"areaServed":["PL","Europe"],"priceRange":"$$$","sameAs":["https://www.facebook.com/marcin4funphotos","https://www.instagram.com/marcin4funphotos","https://www.instagram.com/fotofoodie"],"aggregateRating":{"@type":"AggregateRating","ratingValue":"5.0","reviewCount":"133","bestRating":"5"},"founder":{"@type":"Person","name":"Marcin Kaźmieruk","jobTitle":"Fotograf","award":["#1 Foodelia 2025","IPA 2026","Flash Masters Top 10","Two Mann Studios Scholarship","Osobowość Roku 2025 Jelenia Góra"]},"knowsAbout":["fotografia kulinarna","fotografia komercyjna","fotografia eventowa","fotografia ślubna","fotografia teatralna"]}'%(b,b,b)
    out=[biz]
    if page=="o-mnie.html":
        out.append('{"@context":"https://schema.org","@type":"Person","name":"Marcin Kaźmieruk","jobTitle":"Fotograf","url":"%s/o-mnie.html","knowsLanguage":["pl","en"]}'%b)
    if inner_html and "faq" in inner_html:
        fsoup=BeautifulSoup(inner_html,"html.parser")
        qas=[]
        for det in fsoup.select(".faq details"):
            summ=det.find("summary"); p=det.find("p")
            if summ and p:
                q=summ.get_text(strip=True); a=p.get_text(strip=True)
                qas.append('{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'%(json.dumps(q,ensure_ascii=False),json.dumps(a,ensure_ascii=False)))
        if qas:
            out.append('{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[%s]}'%",".join(qas))
    return "\n".join('<script type="application/ld+json">%s</script>'%o for o in out)

def build(page,lang):
    cfg=pages_cfg[page]
    title=cfg["title_"+lang]; desc=cfg["desc_"+lang]
    ppage=soup.find("div",attrs={"data-page":page})
    inner=transform(ppage.decode_contents(),lang)
    inner=apply_content(inner,lang)
    inner=inner.replace('WEB3KEY_PLACEHOLDER', str(site.get('web3_key','')))
    for tok,(key,default) in IMG_SLOTS.items():
        val=(site.get(key) or default).lstrip('/')
        inner=inner.replace(tok, val)
    for cat in GAL_ALT:                          # wstaw galerie z galleries.yml
        inner=inner.replace(f'<!--GALLERY:{cat}-->', render_gallery(cat))
    if lang=="en":
        inner=re.sub(r'(src|href)="images/', r'\1="../images/', inner)
        cssref=f"../style.css?v={CSS_VER}"; canon=(f"{DOMAIN}/en/" if page=="index.html" else f"{DOMAIN}/en/{page}"); loc="en_GB"; hl="en"
        alt_pl=(f"{DOMAIN}/" if page=="index.html" else f"{DOMAIN}/{page}"); alt_en=canon
    else:
        cssref=f"style.css?v={CSS_VER}"; canon=(f"{DOMAIN}/" if page=="index.html" else f"{DOMAIN}/{page}"); loc="pl_PL"; hl="pl"
        alt_pl=canon; alt_en=(f"{DOMAIN}/en/" if page=="index.html" else f"{DOMAIN}/en/{page}")
    ogimg=f"{DOMAIN}/images/food/51.webp"
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
{FONTS_LINK}
<link rel="stylesheet" href="{cssref}">
{THEME_STYLE}
{jsonld(page,lang,inner)}
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

os.makedirs(os.path.join(OUT,"en"),exist_ok=True)
open(os.path.join(OUT,"style.css"),"w",encoding="utf-8").write(css)
for page in pages_cfg:
    open(os.path.join(OUT,page),"w",encoding="utf-8").write(build(page,"pl"))
    open(os.path.join(OUT,"en",page),"w",encoding="utf-8").write(build(page,"en"))
urls=[]
for page in pages_cfg:
    for pref in ("","en/"):
        loc=(f"{DOMAIN}/{pref}" if page=="index.html" else f"{DOMAIN}/{pref}{page}")
        pr="1.0" if page=="index.html" else ("0.5" if pages_cfg[page].get("noindex") else "0.8")
        urls.append(f"  <url><loc>{loc}</loc><changefreq>monthly</changefreq><priority>{pr}</priority></url>")
open(os.path.join(OUT,"sitemap.xml"),"w",encoding="utf-8").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+"\n".join(urls)+"\n</urlset>\n")
open(os.path.join(OUT,"robots.txt"),"w",encoding="utf-8").write(f"User-agent: *\nAllow: /\nDisallow: /prywatnosc.html\nDisallow: /en/prywatnosc.html\nDisallow: /admin/\n\nSitemap: {DOMAIN}/sitemap.xml\n")

# ---- strona 404 ----
def page_404(lang):
    if lang=="en":
        title="Page not found | Marcin Kaźmieruk Photography"
        h1="Page not found"; p="This page doesn't exist or has moved. Head back to the homepage."
        btn="Back to homepage"; cssref=f"../style.css?v={CSS_VER}"; home="../index.html"
    else:
        title="Nie znaleziono strony | Marcin Kaźmieruk Fotografia"
        h1="404 — nie znaleziono strony"; p="Ta strona nie istnieje albo została przeniesiona. Wróć na stronę główną."
        btn="Wróć na stronę główną"; cssref=f"style.css?v={CSS_VER}"; home="index.html"
    body=f'''<section class="page-hero"><div class="wrap" style="text-align:center">
<h1>{h1}</h1>
<p style="margin:20px auto 34px;max-width:520px">{p}</p>
<a href="{home}" style="display:inline-flex;padding:15px 30px;border:1px solid var(--accent);color:var(--ink);text-decoration:none;text-transform:uppercase;letter-spacing:.1em;font-size:13px;border-radius:2px">{btn}</a>
</div></section>'''
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="robots" content="noindex,follow">
<meta name="theme-color" content="#0a0e1a">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..700&family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{cssref}">
</head>
<body>
{nav_html("404.html",lang)}
<main id="main">{body}</main>
{footer_html(lang)}
{SCRIPT}
</body>
</html>'''

open(os.path.join(OUT,"404.html"),"w",encoding="utf-8").write(page_404("pl"))
open(os.path.join(OUT,"en","404.html"),"w",encoding="utf-8").write(page_404("en"))

for d in ("images","admin"):
    sp=os.path.join(HERE,d)
    if os.path.isdir(sp): shutil.copytree(sp, os.path.join(OUT,d), dirs_exist_ok=True)
hp=os.path.join(HERE,"_headers")
if os.path.isfile(hp): shutil.copy(hp, os.path.join(OUT,"_headers"))
print("OK build ->", OUT)
