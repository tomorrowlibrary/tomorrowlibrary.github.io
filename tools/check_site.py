"""Check local assets, links, fragments, unique IDs and catalogue source paths."""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit
ROOT=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.links=[];self.ids=[];self.h1=0;self.title=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if attrs.get("id"):self.ids.append(attrs["id"])
        if tag=="h1":self.h1+=1
        if tag=="title":self.title+=1
        for key in ["href","src"]:
            if key in attrs:self.links.append(attrs[key])
errors=[]
parsed={}
for path in ROOT.glob("*.html"):
    p=Page();p.feed(path.read_text());parsed[path]=p
    if p.h1!=1 or p.title!=1:errors.append(f"{path.name}: requires one h1/title")
    if len(p.ids)!=len(set(p.ids)):errors.append(f"{path.name}: duplicate IDs")
for path,p in parsed.items():
    for value in p.links:
        u=urlsplit(value)
        if u.scheme or u.netloc:continue
        target=(path.parent/unquote(u.path)).resolve() if u.path else path.resolve()
        if not target.is_relative_to(ROOT):errors.append(f"{path.name}: link escapes site: {value}")
        elif not target.exists():errors.append(f"{path.name}: missing {value}")
        elif u.fragment and target.suffix==".html":
            other=parsed.get(target)
            if other and unquote(u.fragment) not in other.ids:errors.append(f"{path.name}: missing anchor {value}")
for key in ["repositories","code","datasets","papers","competitions","solutions","resources"]:
    items=json.loads((ROOT/"catalogue"/(key+".json")).read_text())
    if key=="datasets" and len({x["id"] for x in items})!=len(items):errors.append("Duplicate dataset IDs")
    for item in items:
        for field in ["url","source_url","download_url","pdf_url","local_url","guide_url"]:
            if not item.get(field):continue
            value=item[field]
            if "example" in urlsplit(value).netloc:errors.append(f"Example URL in {key}: {value}")
            if not urlsplit(value).scheme and not (ROOT/unquote(urlsplit(value).path)).is_file():errors.append(f"Missing catalogue target: {value}")
if errors:
    print("\n".join(errors));sys.exit(1)
print(f"PASS: {len(parsed)} pages; local assets, links, anchors, unique IDs and catalogue targets.")
