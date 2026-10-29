"""Download selected original files from the included Library catalogue.

Examples:
    python download_data.py --list
    python download_data.py --collection "Prosperity 2" --contains round_0 --out data

No selection means list-only. Original source terms are recorded in the catalogue;
availability of a file does not establish redistribution rights.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import urlopen


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue",type=Path,default=Path(__file__).parent/"data-catalogue.json")
    parser.add_argument("--list",action="store_true")
    parser.add_argument("--id")
    parser.add_argument("--collection")
    parser.add_argument("--contains")
    parser.add_argument("--out",type=Path,default=Path("data"))
    args=parser.parse_args()
    items=json.loads(args.catalogue.read_text())
    selected=[d for d in items if (not args.id or d["id"]==args.id)
              and (not args.collection or d["category"]==args.collection)
              and (not args.contains or args.contains.lower() in (d["title"]+" "+d.get("source_path","")).lower())]
    if args.list or not any([args.id,args.collection,args.contains]):
        for d in selected:
            print(d["id"]+" | "+d["category"]+" | "+d["title"])
        print(str(len(selected))+" entries. Add --id or a filter to select downloads.")
        return
    if not selected:parser.error("No files match the selection.")
    args.out.mkdir(parents=True,exist_ok=True)
    for d in selected:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*",d["id"]):raise ValueError("Unsafe dataset ID.")
        address=urlsplit(d["download_url"])
        if address.scheme!="https" or not address.netloc or address.username or address.password:
            raise ValueError("Downloads require a public HTTPS URL without credentials.")
        suffix=Path(urlsplit(d["download_url"]).path).suffix or ".data"
        dest=args.out/(d["id"]+suffix)
        if dest.exists():raise FileExistsError(str(dest)+" already exists; choose another output directory.")
        with urlopen(d["download_url"],timeout=60) as response:
            if urlsplit(response.url).scheme!="https":raise ValueError("Refusing a non-HTTPS redirect.")
            data=response.read()
        if d.get("size_bytes") and len(data)!=d["size_bytes"]:raise ValueError("Size mismatch for "+d["id"])
        blob=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
        if d.get("blob_sha") and blob!=d["blob_sha"]:raise ValueError("Source blob hash mismatch for "+d["id"])
        if d.get("sha256") and hashlib.sha256(data).hexdigest()!=d["sha256"]:raise ValueError("SHA-256 mismatch for "+d["id"])
        dest.write_bytes(data)
        print("Saved "+str(dest))


if __name__=="__main__":
    main()
