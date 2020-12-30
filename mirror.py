import requests
import argparse
import json

from pathlib import Path
import os

# Globals

map_failed = set()
map_ok = set()
map_queue = set()
map_parsed = set()

url_failed = set()
url_ok = set()

file_queue = set()

# Functions

def url_clean(url):
    #return url.replace("//","/").replace("https:/","https://").split("#")[0]
    return url.split("#")[0].strip()

def url_to_filename(url):
    return url.replace("//","/").replace("https:/","/").split("#")[0]

def url_to_new_exiturl(url):
    return url.replace("//","/").replace("https:/","/")

def check_map_url(url):
    if url in map_failed:
        return False
    if url in map_ok:
        return True

    try:
        r = requests.head(url)
    except requests.exceptions.ConnectionError:
        map_failed.add(url)
        return False

    if r.ok:
        map_ok.add(url)
        map_queue.add(url)
        return True
    else:
        map_failed.add(url)
        return False

def check_generic_url(url):
    if url in url_failed:
        return False
    if url in url_ok:
        return True

    try:
        r = requests.head(url)
    except requests.exceptions.ConnectionError:
        url_failed.add(url)
        return False

    if r.ok:
        url_ok.add(url)
        return True
    else:
        url_failed.add(url)
        return False

def parse_map(url, target, print_success = False, tilesets = False):
    if url in map_parsed:
        try:
            map_queue.remove(url)
        except KeyError:
            pass
        return

    if print_success:
        print(url)

    has_error = False
    try:
        r = requests.get(url)
    except:
        print("  ! HTTP error")
        map_parsed.add(url)
        try:
            map_queue.remove(url)
        except KeyError:
            pass
        return

    try:
        data = r.json()
    except json.decoder.JSONDecodeError:



        if not print_success:
            print(url)
        print("  ! invalid JSON")
        map_parsed.add(url)
        try:
            map_queue.remove(url)
        except KeyError:
            pass
        return


    for layer in data["layers"]:
        if "properties" in layer:
            for prop in layer["properties"]:
                if prop["name"] == "exitSceneUrl" or prop["name"] == "exitUrl":
                    next = requests.compat.urljoin(url, prop["value"])

                    map_queue.add(url_clean(next))

                    prop["value"] = url_to_new_exiturl(next)
            if prop["name"] == "playAudio" or prop["name"] == "playAudioLoop":
                if not prop["value"].startswith("stream:"):
                    file_url = requests.compat.urljoin(url, prop["value"])
                    file_queue.add(file_url)


    try:
        for tileset in data["tilesets"]:
            ts_url = requests.compat.urljoin(url, tileset["image"])
            file_queue.add(ts_url)
    except:
        pass


    local_filename = target + url_to_filename(url)
    local_dir = os.path.dirname(local_filename)
    Path(local_dir).mkdir(parents=True, exist_ok=True)
    with open(local_filename, 'w') as outfile:
        json.dump(data, outfile)

    map_parsed.add(url)
    try:
        map_queue.remove(url)
    except KeyError:
        pass

def download_file(url,target):
    local_filename = target + url_to_filename(url)
    if Path(local_filename).exists():
        return

    local_dir = os.path.dirname(local_filename)
    Path(local_dir).mkdir(parents=True, exist_ok=True)
    print("%s -> %s" % (url, local_filename))
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk:
                f.write(chunk)


parser = argparse.ArgumentParser(description='Validate rC3.world maps')
parser.add_argument("url", help="URL of the map to parser")
parser.add_argument('--recursive', "-r", action="store_true",
                    help='Recurse into other maps')
parser.add_argument("--verbose", "-v", action="store_true",
                    help='Print successes as well as failures')
parser.add_argument("--tilesets", "-t", action="store_true",
                    help='Check tilesets as well')

args = parser.parse_args()

#start = "https://lobby.maps.at.rc3.world//maps/erfas-south.json"

target = "out"

url = url_clean(args.url)

parse_map(url, target, args.verbose, args.tilesets)

if args.recursive:
    while len(map_queue) > 0:
        for url in list(map_queue):
            parse_map(url, target, args.verbose, args.tilesets)

for file_url in file_queue:
    try:
        if ".maps.at.rc3.world" not in file_url:
            continue
        download_file(file_url, target)
    except:
        print("fail")
        pass
