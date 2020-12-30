# rc3.world map mirror maker

Create your own mirror of the rC3.world

## howto
```
git clone https://github.com/tiefpunkt/rc3-world-map-mirror.git
cd rc3-world-map-mirror
python3 -mvenv env
. env/bin/activate
pip install -r requirements.txt
python mirror.py -r https://lobby.maps.at.rc3.world/main.json
```
