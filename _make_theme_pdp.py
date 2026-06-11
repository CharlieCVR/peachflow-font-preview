#!/usr/bin/env python3
"""Generate the Shopify product page sections from the product.html mockup."""
import re, pathlib

ROOT = pathlib.Path(".")
B = ROOT / "_theme-build"
t = (ROOT / "product.html").read_text()

def block(start, end):
    i = t.index(start); j = t.index(end, i)
    return t[i:j]

def schema(name):
    return ('\n{% schema %}\n{\n  "name": "' + name + '",\n  "settings": [],\n  "presets": [{ "name": "' + name + '" }]\n}\n{% endschema %}\n')

# ---------- product page CSS (full mockup product stylesheet, fonts come from theme) ----------
style = re.search(r"<style>(.*?)</style>", t, re.S).group(1)
style = re.sub(r"@font-face\{[^}]*\}", "", style)
(B / "assets/pf-product.css.liquid").write_text(style)

# ---------- main PDP section ----------
pdp = block('<section class="pdp">', '<!-- STAT BAND -->')

# gallery -> product media
gal = re.search(r'<div class="gallery">.*?</div>\s*</div>\n', pdp, re.S).group(0)
new_gal = '''<div class="gallery">
        <div class="gframe"><img id="galMain" src="{{ product.featured_image | image_url: width: 1100 }}" alt="{{ product.featured_image.alt | escape }}"></div>
        <div class="gal-thumbs">
          {%- for media in product.media limit: 6 -%}
          <button class="gal-thumb{% if forloop.first %} active{% endif %}" data-src="{{ media | image_url: width: 1100 }}"><img src="{{ media | image_url: width: 200 }}" alt="{{ media.alt | escape }}" loading="lazy"></button>
          {%- endfor -%}
        </div>
      </div>
'''
pdp = pdp.replace(gal, new_gal)

# title / sub / price
pdp = re.sub(r"<h1>[^<]*</h1>", "<h1>{{ product.title | split: ' - ' | first }}</h1>", pdp, count=1)
pdp = pdp.replace('<div class="pdp-price">£14.99</div>', '<div class="pdp-price">{{ product.price | money }}</div>')

# breadcrumb if present
pdp = pdp.replace('href="index.html"', 'href="{{ routes.root_url }}"').replace('href="shop.html"', 'href="{{ routes.all_products_collection_url }}"')
pdp = re.sub(r'(<a [^>]*class="[^"]*crumb[^"]*"[^>]*>Watermelons</a>|Watermelons</span>)', "{{ product.title | split: ' - ' | first }}</span>", pdp)

# multi-buy options with Liquid maths
opts_old = re.search(r'<div class="opt sel".*?£44\.97</span></div>\n?', pdp, re.S).group(0)
opts_new = '''{%- assign base = product.price -%}
{%- assign two_each = base | times: 0.85 | round -%}
{%- assign two_total = two_each | times: 2 -%}
{%- assign four_each = base | times: 0.75 | round -%}
{%- assign four_total = four_each | times: 4 -%}
        <div class="opt sel" data-qty="1"><span class="radio"></span><span class="otext"><b>One pair</b><small>Just the essentials</small></span><span class="oprice">{{ base | money }}</span></div>
        <div class="opt" data-qty="2"><span class="radio"></span><span class="otext"><b>Two pairs <span class="obadge">Save 15%</span></b><small>{{ two_each | money }} each &middot; free UK shipping</small></span><span class="oprice">{{ two_total | money }}</span></div>
        <div class="opt" data-qty="4"><span class="radio"></span><span class="otext"><b>Four pairs <span class="obadge">Most popular</span></b><small>{{ four_each | money }} each &middot; 25% off</small></span><span class="oprice">{{ four_total | money }}</span></div>
'''
pdp = pdp.replace(opts_old, opts_new)

# stock line conditional on tag
pdp = pdp.replace('<div class="stockline">Low stock, selling fast</div>',
                  "{% if product.available and product.tags contains 'low-stock' %}<div class=\"stockline\">Low stock, selling fast</div>{% endif %}")

# buy bar -> real product form
buybar_old = re.search(r'<div class="buybar">.*?</div>\n', pdp, re.S).group(0)
buybar_new = '''{% form 'product', product, id: 'pf-product-form' %}
        <input type="hidden" name="id" value="{{ product.selected_or_first_available_variant.id }}">
        <input type="hidden" name="quantity" id="pfQty" value="1">
        <div class="buybar">
          <div class="qty-stepper"><button type="button" id="qdec" aria-label="Decrease">&minus;</button><span class="qv" id="qv">1</span><button type="button" id="qinc" aria-label="Increase">+</button></div>
          <button type="submit" class="atc" id="atc" {% unless product.available %}disabled style="opacity:.55;cursor:not-allowed"{% endunless %}>{% if product.available %}Add to bag &middot; {{ product.price | money }}{% else %}Sold out{% endif %}</button>
        </div>
        {% endform %}
'''
pdp = pdp.replace(buybar_old, buybar_new)
pdp = pdp.replace('href="bundle.html"', 'href="#"')
pdp = pdp.replace('href="size-guide.html"', 'href="#"')

JS = '''
<script>
(function(){
  var main=document.getElementById('galMain');
  document.querySelectorAll('.gal-thumb').forEach(function(thumb){thumb.addEventListener('click',function(){
    document.querySelectorAll('.gal-thumb').forEach(function(x){x.classList.remove('active');});
    thumb.classList.add('active'); main.src=thumb.dataset.src;
  });});
  {% if product.available %}
  var qty=1, price={{ product.price | divided_by: 100.0 }};
  var form=document.getElementById('pf-product-form'), atc=document.getElementById('atc');
  function fmt(n){return '{{ cart.currency.symbol | default: "£" }}'+n.toFixed(2);}
  function tierPct(q){var p=0;[[2,15],[4,25],[6,35],[8,40],[10,45]].forEach(function(x){if(q>=x[0])p=x[1];});return p;}
  function render(){
    var pct=tierPct(qty), tot=price*qty*(1-pct/100);
    atc.textContent='Add to bag \\u00b7 '+fmt(tot)+(pct>0?' ('+pct+'% off)':'');
    document.getElementById('qv').textContent=qty;
    document.getElementById('pfQty').value=qty;
    var sa=document.getElementById('saBtn'); if(sa) sa.textContent=atc.textContent;
  }
  document.querySelectorAll('.opt').forEach(function(o){o.addEventListener('click',function(){
    document.querySelectorAll('.opt').forEach(function(x){x.classList.remove('sel');});
    o.classList.add('sel'); qty=parseInt(o.dataset.qty); render();
  });});
  document.getElementById('qdec').addEventListener('click',function(){if(qty>1){qty--;render();}});
  document.getElementById('qinc').addEventListener('click',function(){qty++;render();});
  form.addEventListener('submit',function(e){
    e.preventDefault();
    document.getElementById('pfQty').value=qty;
    var fd=new FormData(form);
    fetch('{{ routes.cart_add_url }}.js',{method:'POST',body:fd}).then(function(r){
      if(!r.ok) throw new Error('add failed');
      return fetch('{{ routes.cart_url }}.js');
    }).then(function(r){return r.json();}).then(function(c){
      document.querySelectorAll('.bag-count').forEach(function(b){b.textContent=c.item_count;});
      var old=atc.textContent; atc.textContent='Added \\u2713';
      setTimeout(function(){atc.textContent=old;},1600);
    }).catch(function(){ atc.textContent='Could not add, try again'; });
  });
  render();
  {% endif %}
  var bar=document.getElementById('stickyAtc');
  if(bar){
    var buy=document.querySelector('.buybar');
    var sbtn=document.getElementById('saBtn');
    if(sbtn) sbtn.addEventListener('click',function(){ document.getElementById('atc').click(); });
    if('IntersectionObserver' in window && buy){
      new IntersectionObserver(function(en){
        var e=en[0]; bar.classList.toggle('show', !e.isIntersecting && e.boundingClientRect.top<0);
      },{threshold:0}).observe(buy);
    }
  }
})();
</script>
'''
STICKY = '''<div class="sticky-atc" id="stickyAtc">
  <img src="{{ product.featured_image | image_url: width: 120 }}" alt="">
  <div class="si"><b>{{ product.title | split: ' - ' | first }}</b><span>{% if product.available %}Free UK shipping over &pound;25{% else %}Sold out{% endif %}</span></div>
  <button id="saBtn" {% unless product.available %}disabled{% endunless %}>Add to bag &middot; {{ product.price | money }}</button>
</div>
'''
head = "{{ 'pf-product.css' | asset_url | stylesheet_tag }}\n"
(B / "sections/pf-product.liquid").write_text(head + pdp + STICKY + JS + schema("PF Product"))

# ---------- stats band ----------
stats = block('<!-- STAT BAND -->', '<!-- REVIEWS -->')
(B / "sections/pf-pdp-stats.liquid").write_text(stats + schema("PF Product Stats"))

# ---------- reviews ----------
rev = block('<!-- REVIEWS -->', '<!-- FAQ -->')
(B / "sections/pf-reviews.liquid").write_text(rev + schema("PF Reviews"))

# ---------- faq ----------
pfaq = block('<!-- FAQ -->', '<!-- CROSS-SELL -->')
(B / "sections/pf-pdp-faq.liquid").write_text(pfaq + schema("PF Product FAQ"))

# ---------- cross-sell ----------
xs_head = block('<!-- CROSS-SELL -->', '<a class="card"')
xs_head = xs_head.replace('href="shop.html"', 'href="{{ routes.all_products_collection_url }}"')
xs = xs_head + '''
{%- assign shown = 0 -%}
{%- for p in collections['all'].products -%}
  {%- if p.id == product.id or shown >= 4 -%}{%- continue -%}{%- endif -%}
  {% render 'pf-product-card', card_product: p %}
  {%- assign shown = shown | plus: 1 -%}
{%- endfor -%}
    </div>
  </div>
</section>
''' + schema("PF Cross Sell")
(B / "sections/pf-xsell.liquid").write_text(xs)

# ---------- template ----------
import json
(B / "templates/product.json").write_text(json.dumps({
  "sections": {
    "pf_product": {"type": "pf-product", "settings": {}},
    "pf_stats": {"type": "pf-pdp-stats", "settings": {}},
    "pf_reviews": {"type": "pf-reviews", "settings": {}},
    "pf_faq": {"type": "pf-pdp-faq", "settings": {}},
    "pf_xsell": {"type": "pf-xsell", "settings": {}},
    "pf_instagram": {"type": "pf-instagram", "settings": {}}
  },
  "order": ["pf_product", "pf_stats", "pf_reviews", "pf_faq", "pf_xsell", "pf_instagram"]
}, indent=2))

for n in ["assets/pf-product.css.liquid","sections/pf-product.liquid","sections/pf-pdp-stats.liquid",
          "sections/pf-reviews.liquid","sections/pf-pdp-faq.liquid","sections/pf-xsell.liquid","templates/product.json"]:
    print(n, (B / n).stat().st_size // 1024, "KB")
