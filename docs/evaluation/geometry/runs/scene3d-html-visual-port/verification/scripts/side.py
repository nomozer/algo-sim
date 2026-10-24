import json, sys
from PIL import Image, ImageDraw
o = sys.argv[1]
r = json.load(open(f'{o}/receipt.json', encoding='utf-8'))
for row in r['rows']:
    a = Image.open(f"{o}/{row['html']['file']}").convert('RGB'); b = Image.open(f"{o}/{row['algosim']['file']}").convert('RGB')
    h = max(a.height, b.height); c = Image.new('RGB', (a.width + b.width + 12, h + 26), 'white')
    c.paste(a, (0, 26)); c.paste(b, (a.width + 12, 26)); d = ImageDraw.Draw(c)
    d.text((6, 6), f"HTML reference (unmodified): {row['html']['shape']}", fill='black')
    d.text((a.width + 18, 6), f"AlgoSim: {row['algosim']['case']} (same figure-relative view)", fill='black')
    name = f"SIDE-{row['html']['shape']}-{row['viewport'].split('x')[0]}.png"; c.save(f'{o}/{name}'); row['side_by_side'] = name
json.dump(r, open(f'{o}/receipt.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok')
