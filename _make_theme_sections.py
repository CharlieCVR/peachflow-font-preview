#!/usr/bin/env python3
"""Generate Shopify theme sections from the mockup markup (1:1 design port)."""
import re, pathlib

ROOT = pathlib.Path(".")
B = ROOT / "_theme-build"
t = (ROOT / "index.html").read_text()

def block(start, end):
    i = t.index(start)
    j = t.index(end, i)
    return t[i:j]

def schema(name):
    return ('\n{% schema %}\n{\n  "name": "' + name + '",\n  "settings": [],\n  "presets": [{ "name": "' + name + '" }]\n}\n{% endschema %}\n')

# ---------- header (announce + nav + logo defs + mobile drawer) ----------
hdr = block('<div class="announce"', '</header>') + '</header>'
drawer = block('<div class="drawer" id="pfdrawer">', '<div class="cartdrawer"')
logo_defs = (B / "snippets/pf-logo-defs.liquid").read_text()

hdr = hdr.replace('<a href="#" aria-label="Peach & Flow home"', '<a href="{{ routes.root_url }}" aria-label="Peach & Flow home"')
hdr = hdr.replace('<a href="shop.html">Shop All</a>', '<a href="{{ routes.all_products_collection_url }}">Shop All</a>')
hdr = hdr.replace('<a href="bundle.html">Bundle Builder</a>', '<a href="/pages/bundle">Bundle Builder</a>')
hdr = hdr.replace('<a href="#">Search</a>', '<a href="{{ routes.search_url }}">Search</a>')
hdr = hdr.replace('<a href="#">Account</a>', '<a href="{{ routes.account_url }}">Account</a>')
hdr = re.sub(r'<span class="bag">Bag <span class="bag-count">\d+</span></span>',
             '<a class="bag" href="{{ routes.cart_url }}">Bag <span class="bag-count">{{ cart.item_count }}</span></a>', hdr)
PAGE_LINKS = [('href="shop.html"', 'href="{{ routes.all_products_collection_url }}"'),
             ('href="bundle.html"', 'href="/pages/bundle"'),
             ('href="our-story.html"', 'href="/pages/our-story"'), ('href="wholesale.html"', 'href="/pages/wholesale"'),
             ('href="shipping.html"', 'href="/pages/shipping"'), ('href="returns.html"', 'href="/pages/returns"'),
             ('href="size-guide.html"', 'href="/pages/size-guide"'), ('href="contact.html"', 'href="/pages/contact"')]
for a, b in PAGE_LINKS:
    drawer = drawer.replace(a, b)
(B / "sections/pf-header.liquid").write_text(
    "{% render 'pf-logo-defs' %}\n" + hdr + "\n" + drawer + schema("PF Header"))

# ---------- hero ----------
hero = block('<!-- HERO -->', '<!-- PRESS MARQUEE -->')
hero = hero.replace('src="assets/hero-main.jpg"', 'src="{{ \'pf-hero-main.jpg\' | asset_url }}"')
hero = hero.replace('href="shop.html"', 'href="{{ routes.all_products_collection_url }}"')
hero = hero.replace('href="bundle.html"', 'href="#"')
(B / "sections/pf-hero.liquid").write_text(hero + schema("PF Hero"))

# ---------- marquee ----------
mq = block('<!-- PRESS MARQUEE -->', '<!-- PRODUCT GRID -->')
(B / "sections/pf-marquee.liquid").write_text(mq + schema("PF Press Marquee"))

# ---------- product grid: real product loop ----------
grid_head = '''<!-- PRODUCT GRID -->
<section class="section" id="shop">
  <div class="wrap">
    <div class="sec-head">
      <div>
        <h2>The Collection</h2>
      </div>
      <a class="sec-link" href="{{ section.settings.collection.url | default: routes.all_products_collection_url }}">View all socks &rarr;</a>
    </div>
    <div class="grid">
{%- assign col = section.settings.collection | default: collections['all'] -%}
{%- for product in col.products limit: 8 -%}
      <a class="card" href="{{ product.url }}">
        <div class="card-img">
          {%- if product.available == false -%}<span class="badge out">Sold out</span>
          {%- elsif product.tags contains 'bestseller' -%}<span class="badge terra">Bestseller</span>
          {%- elsif product.tags contains 'low-stock' -%}<span class="badge">Low stock</span>
          {%- else -%}<span class="badge">In stock</span>{%- endif -%}
          <div class="ph">{{ product.featured_image | image_url: width: 600 | image_tag: alt: product.title, loading: 'lazy' }}</div>
          <div class="quick">{% if product.available %}+ Add to bag{% else %}Notify me{% endif %}</div>
        </div>
        <div class="card-body"><h3>{{ product.title }}</h3><div class="card-meta"><span class="price">{{ product.price | money }}</span><span>&#9733; 4.9</span></div></div>
      </a>
{%- endfor -%}
    </div>
  </div>
</section>
{% schema %}
{
  "name": "PF Collection Grid",
  "settings": [
    { "type": "collection", "id": "collection", "label": "Collection" }
  ],
  "presets": [{ "name": "PF Collection Grid" }]
}
{% endschema %}
'''
(B / "sections/pf-collection.liquid").write_text(grid_head)

# ---------- bundle teaser ----------
bt = block('<!-- BUNDLE TEASER -->', '<!-- US VS THEM -->')
bt = bt.replace('href="bundle.html"', 'href="#"')
(B / "sections/pf-bundle-teaser.liquid").write_text(bt + schema("PF Bundle Teaser"))

# ---------- comparison ----------
vs = block('<!-- US VS THEM -->', '<!-- TESTIMONIALS -->')
(B / "sections/pf-comparison.liquid").write_text(vs + schema("PF Comparison Table"))

# ---------- testimonials ----------
ts = block('<!-- TESTIMONIALS -->', '<!-- SOCIAL')
(B / "sections/pf-testimonials.liquid").write_text(ts + schema("PF Testimonials"))

# ---------- instagram ----------
ig = block('<!-- SOCIAL', '<!-- FAQ -->')
for n in range(1, 13):
    ig = ig.replace(f'src="assets/instagram/ig{n}.jpg"', "src=\"{{ 'pf-ig-%d.jpg' | asset_url }}\"" % n)
ig = ig.replace('<a class="social-follow" href="#">', '<a class="social-follow" href="https://www.instagram.com/peachandflow_/" target="_blank" rel="noopener">')
(B / "sections/pf-instagram.liquid").write_text(ig + schema("PF Instagram"))

# ---------- faq ----------
faq = block('<!-- FAQ -->', '<!-- CLOSING CTA -->')
(B / "sections/pf-faq.liquid").write_text(faq + schema("PF FAQ"))

# ---------- closing ----------
cl = block('<!-- CLOSING CTA -->', '<!-- FOOTER -->')
cl = cl.replace('href="shop.html"', 'href="{{ routes.all_products_collection_url }}"')
cl = cl.replace('href="bundle.html"', 'href="#"')
(B / "sections/pf-closing.liquid").write_text(cl + schema("PF Closing CTA"))

# ---------- footer ----------
ft = block('<!-- FOOTER -->', '</footer>') + '</footer>'
for a, b in [('href="shop.html"', 'href="{{ routes.all_products_collection_url }}"'),
             ('href="bundle.html"', 'href="/pages/bundle"'),
             ('href="our-story.html"', 'href="/pages/our-story"'), ('href="wholesale.html"', 'href="/pages/wholesale"'),
             ('href="shipping.html"', 'href="/pages/shipping"'),
             ('href="returns.html"', 'href="/pages/returns"'),
             ('href="size-guide.html"', 'href="/pages/size-guide"'), ('href="contact.html"', 'href="/pages/contact"'),
             ('href="terms-of-service.html"', 'href="/pages/terms-of-service"'),
             ('href="privacy-policy.html"', 'href="/pages/privacy-policy"')]:
    ft = ft.replace(a, b)
# native payment icons
ft = re.sub(r'<div class="paymarks">.*?</div>',
            '<div class="paymarks">{% for type in shop.enabled_payment_types %}{{ type | payment_type_svg_tag: class: \'pf-paymark\' }}{% endfor %}</div>',
            ft, flags=re.S)
(B / "sections/pf-footer.liquid").write_text(ft + schema("PF Footer"))

# ---------- group + template JSON ----------
import json
(B / "sections/header-group.json").write_text(json.dumps({
  "type": "header", "name": "Header group",
  "sections": { "pf_header": { "type": "pf-header", "settings": {} } },
  "order": ["pf_header"]
}, indent=2))
(B / "sections/footer-group.json").write_text(json.dumps({
  "type": "footer", "name": "Footer group",
  "sections": { "pf_footer": { "type": "pf-footer", "settings": {} } },
  "order": ["pf_footer"]
}, indent=2))
secs = ["pf-hero","pf-marquee","pf-collection","pf-bundle-teaser","pf-comparison","pf-testimonials","pf-instagram","pf-faq","pf-closing"]
(B / "templates/index.json").write_text(json.dumps({
  "sections": { s.replace("-", "_"): { "type": s, "settings": {} } for s in secs },
  "order": [s.replace("-", "_") for s in secs]
}, indent=2))

# extra CSS for paymark svgs
css = (B / "assets/peachflow.css.liquid").read_text()
if ".pf-paymark" not in css:
    (B / "assets/peachflow.css.liquid").write_text(css + "\n.pf-paymark{height:24px;width:auto;border-radius:4px}\n.paymarks svg{height:24px;width:auto;border-radius:4px}\n")

for p in sorted(B.rglob("*")):
    if p.is_file(): print(f"{p.relative_to(B)}  ({p.stat().st_size//1024} KB)")
