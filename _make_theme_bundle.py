#!/usr/bin/env python3
"""Port the bundle builder page into a Shopify section + page template.
Injects real variant IDs and wires 'Add bundle to cart' to the live cart."""
import re, json, pathlib
ROOT = pathlib.Path(".")
B = ROOT / "_theme-build"
t = (ROOT / "bundle.html").read_text()

# data-id (mockup) -> real Shopify variant id
VARIANTS = {
    "matcha":      56082710298950,
    "eggs":        56082686345542,
    "watermelons": 56082690015558,
    "peaches":     56082701549894,
    "flowers":     56082694340934,
    "chilis":      56082699288902,
    "hottie":      56082702565702,
    "smiley":      56082705154374,
}

# ---- bundle CSS asset ----
style = re.search(r"<style>(.*?)</style>", t, re.S).group(1)
style = re.sub(r"@font-face\{[^}]*\}", "", style)
(B / "assets/pf-bundle.css.liquid").write_text(style)

# ---- content ----
content = t[t.index('</header>') + len('</header>'): t.index('<footer>')].strip()
for a, b in [('href="shop.html"', 'href="{{ routes.all_products_collection_url }}"'),
             ('href="index.html"', 'href="{{ routes.root_url }}"'),
             ('href="contact.html"', 'href="/pages/contact"'),
             ('href="size-guide.html"', 'href="/pages/size-guide"')]:
    content = content.replace(a, b)
# static per-card price label -> live price
content = content.replace('<span class="bprice">£14.99</span>',
                          "<span class=\"bprice\">{{ collections['all'].products.first.price | money }}</span>")

# ---- mobile sticky bar (lives after </footer> in the mockup, pull it in) ----
bsticky = t[t.index('<div class="bsticky"'): t.index('</div>\n<script>', t.index('<div class="bsticky"')) + len('</div>')]

# ---- scripts ----
scripts = re.findall(r"<script>.*?</script>", t, re.S)
builder = scripts[0]
sticky = scripts[1] if len(scripts) > 1 else ""

# real price from live product (keeps in sync with the store), fallback 13.99
builder = builder.replace("var PRICE=14.99;",
    "var PRICE={{ collections['all'].products.first.price | default: 1399 | divided_by: 100.0 }};")

# inject the variant map right after the IIFE opens
varmap = "var VARIANTS=" + json.dumps(VARIANTS) + ";"
builder = builder.replace("(function(){", "(function(){\n  " + varmap, 1)

# wire the checkout button: add all bundle items to the real cart, then go to /cart
checkout_js = """
  document.getElementById('checkout').addEventListener('click',function(){
    var items=[]; for(var k in bundle){ if(bundle[k]>0 && VARIANTS[k]) items.push({id:VARIANTS[k], quantity:bundle[k]}); }
    if(!items.length) return;
    var btn=this; btn.disabled=true; var label=btn.textContent; btn.textContent='Adding…';
    fetch('{{ routes.cart_add_url }}.js',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({items:items})})
      .then(function(r){ if(!r.ok) throw new Error('add'); window.location='{{ routes.cart_url }}'; })
      .catch(function(){ btn.disabled=false; btn.textContent='Could not add, try again'; setTimeout(function(){btn.textContent=label;},1800); });
  });
  render();
})();
</script>"""
# replace the trailing  render();\n})();\n</script>  with our wired version
builder = re.sub(r"\n\s*render\(\);\s*\n\}\)\(\);\s*\n</script>\s*$", checkout_js, builder)

def schema(name):
    return ('\n{% schema %}\n{\n  "name": "' + name + '",\n  "settings": [],\n  "presets": [{ "name": "' + name + '" }]\n}\n{% endschema %}\n')

head = "{{ 'pf-bundle.css' | asset_url | stylesheet_tag }}\n"
(B / "sections/pf-bundle.liquid").write_text(head + content + "\n" + bsticky + "\n" + builder + "\n" + sticky + schema("PF Bundle Builder"))
(B / "templates/page.bundle.json").write_text(json.dumps({
    "sections": {"main": {"type": "pf-bundle", "settings": {}}},
    "order": ["main"]
}, indent=2))

# checks
out = (B / "sections/pf-bundle.liquid").read_text()
assert "VARIANTS" in out and "routes.cart_add_url" in out, "wiring missing"
assert "14.99" not in out, "static price leaked"
assert ".html\"" not in out, "leftover .html link"
print("pf-bundle.liquid", len(out)//1024, "KB | css", (B/'assets/pf-bundle.css.liquid').stat().st_size//1024, "KB")
print("variant map injected, checkout wired, price -> live ✓")
