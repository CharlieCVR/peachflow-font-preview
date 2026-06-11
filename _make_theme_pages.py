#!/usr/bin/env python3
"""Port the static content pages (our-story, wholesale, shipping, returns, size-guide,
contact, privacy-policy, terms-of-service) into Shopify page templates + sections."""
import re, json, pathlib
ROOT = pathlib.Path(".")
B = ROOT / "_theme-build"

# every internal .html link -> Shopify route / page url
LINKMAP = [
    ('href="index.html"', 'href="{{ routes.root_url }}"'),
    ('href="shop.html"', 'href="{{ routes.all_products_collection_url }}"'),
    ('href="bundle.html"', 'href="/pages/bundle"'),
    ('href="our-story.html"', 'href="/pages/our-story"'),
    ('href="wholesale.html"', 'href="/pages/wholesale"'),
    ('href="shipping.html"', 'href="/pages/shipping"'),
    ('href="returns.html"', 'href="/pages/returns"'),
    ('href="size-guide.html"', 'href="/pages/size-guide"'),
    ('href="contact.html"', 'href="/pages/contact"'),
    ('href="terms-of-service.html"', 'href="/pages/terms-of-service"'),
    ('href="privacy-policy.html"', 'href="/pages/privacy-policy"'),
]

def relink(s):
    for a, b in LINKMAP:
        s = s.replace(a, b)
    return s

def content_of(fname):
    t = (ROOT / fname).read_text()
    i = t.index('</header>') + len('</header>')
    j = t.index('<footer>')
    return t[i:j].strip()

def schema(name):
    return ('\n{% schema %}\n{\n  "name": "' + name + '",\n  "settings": [],\n  "presets": [{ "name": "' + name + '" }]\n}\n{% endschema %}\n')

# ---- Shopify contact-form wiring ---------------------------------------------
def wire_contact_form(html, success_msg):
    # add name= to each labelled control, derived from its <span class="flabel">LABEL</span>
    LABEL_TO_NAME = {
        "Your name": "contact[name]",
        "Email address": "contact[email]",
        "How can we help?": "contact[body]",
        "Studio / store name": "contact[Studio or store]",
        "Website or Instagram": "contact[Website or Instagram]",
        "Business type": "contact[Business type]",
        "Monthly volume": "contact[Monthly volume]",
        "About you": "contact[body]",
    }
    def add_name(m):
        label = m.group("label").strip()
        tag = m.group("tag")
        nm = LABEL_TO_NAME.get(label)
        if not nm:
            return m.group(0)
        # email control needs type=email already; just insert name + required on core fields
        req = ' required' if nm in ("contact[name]", "contact[email]", "contact[body]") else ''
        return m.group("pre") + '<' + tag + ' name="' + nm + '"' + req + m.group("rest")
    pat = re.compile(
        r'(?P<pre><span class="flabel">(?P<label>[^<]+)</span>)<(?P<tag>input|textarea|select)(?P<rest>[ >])',
    )
    html = pat.sub(add_name, html)
    # convert the dead <form onsubmit="return false" ...> into a real Shopify form
    html = re.sub(
        r'<form onsubmit="return false"([^>]*)>',
        r"{% form 'contact' %}{% if form.posted_successfully? %}<p class='form-success'>"
        + success_msg + r"</p>{% endif %}<div\1>",
        html, count=1)
    # close: the matching </form> -> </div>{% endform %}
    html = html.replace('</form>', '</div>{% endform %}', 1)
    return html

# ---- page definitions --------------------------------------------------------
PAGES = [
    ("our-story.html",       "our-story",        "PF Page Our Story",   None),
    ("wholesale.html",       "wholesale",        "PF Page Wholesale",
        "Thanks! Your wholesale enquiry is in, we'll be in touch within 2 working days."),
    ("shipping.html",        "shipping",         "PF Page Shipping",    None),
    ("returns.html",         "returns",          "PF Page Returns",     None),
    ("size-guide.html",      "size-guide",       "PF Page Size Guide",  None),
    ("contact.html",         "contact",          "PF Page Contact",
        "Thanks! Your message has been sent, we'll get back to you soon."),
    ("privacy-policy.html",  "privacy-policy",   "PF Page Privacy",     None),
    ("terms-of-service.html","terms-of-service", "PF Page Terms",       None),
]

made = []
for fname, handle, secname, success in PAGES:
    body = relink(content_of(fname))
    if success:  # contact / wholesale: wire the real form
        body = wire_contact_form(body, success)
    sec_file = f"pf-page-{handle}"
    (B / f"sections/{sec_file}.liquid").write_text(body + schema(secname))
    (B / f"templates/page.{handle}.json").write_text(json.dumps({
        "sections": {"main": {"type": sec_file, "settings": {}}},
        "order": ["main"]
    }, indent=2))
    made.append((handle, sec_file))
    print(f"{handle:18s} -> sections/{sec_file}.liquid  +  templates/page.{handle}.json"
          f"  ({(B / f'sections/{sec_file}.liquid').stat().st_size} B)")

# sanity: no leftover .html links, forms wired
for handle, sec in made:
    txt = (B / f"sections/{sec}.liquid").read_text()
    assert '.html"' not in txt, f"leftover .html link in {sec}"
print("\nAll content pages generated, links clean ✓")
print("Handles:", ", ".join(h for h, _ in made))
