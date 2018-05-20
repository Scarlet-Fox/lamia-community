from bs4 import BeautifulSoup
from urllib.request import urlopen
import sys, os, glob, lxml, slugify, json

emoji_html_data = urlopen('https://unicode.org/emoji/charts/full-emoji-list.html').read()

# try:
#     emoji_dir = sys.argv[1]
# except IndexError:
#     print("Please provide a path to your emoji files.")
#     sys.exit(99)

# if not os.path.exists(emoji_dir):
#     print("Check your emoji file path... It doesn\'t look right.")
#     sys.exit(99)
#
# local_emoji_files = [e.split("/")[-1] for e in glob.glob(os.path.join(emoji_dir,"*"))]
# local_emoji_files = [e.split(".")[0] for e in local_emoji_files]

emoji_soup = BeautifulSoup(emoji_html_data, "lxml")	
emoji_table = emoji_soup.findChildren('table')[0]
emoji_rows = emoji_table.findChildren('tr')

# def emoji_exists_in_filesystem(unicode_text):
#     return os.path.exists(os.path.join(emoji_dir, unicode_text+".png"))

to_export = []

for row in emoji_rows:
    cells = row.findChildren('td')
    emoji_exists = True
    emoji_description = ""
    emoji_slug = ""
    emoji_unicode = ""
    unicode_text = ""
    
    for i, cell in enumerate(cells):
        if i == 1:
            unicode_text = cell.string.split(" ")[0].lower().replace("u+", "")
            # emoji_exists = emoji_exists_in_filesystem(unicode_text)
        
        if i == 2:
            emoji_unicode = cell.string
            
        if i == 14:
            emoji_description = cell.string
            emoji_slug = slugify.slugify(cell.string).replace("-", "_")
    
    if emoji_exists:
        to_export.append({
            "description": emoji_description,
            "unicode": emoji_unicode,
            "name": emoji_slug
            # "file": unicode_text
        })
    
json_to_export = json.dumps(to_export, indent=4)

output_file = open("emoji.js", "w")
output_file.write(json_to_export)
output_file.close()