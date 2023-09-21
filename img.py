import os
import json
import re
from PIL import Image

file = input("Please enter the location of the image file: ")
if not os.path.isfile(file):
    print('Invalid file location! Make sure the file exists.')
    exit()

data = json.load(open('./leveldata.json'))

tiles = {1: 917, 2: 916, 4: 211, 8: "211,32,2", 16: "211,32,4"}
gdLevels = os.environ.get('HOME') or os.environ.get('USERPROFILE') + '/AppData/Local/GeometryDash/CCLocalLevels.dat'

img = Image.open('./' + file)
pixels = {1: {}}
image_size = img.size[0] * img.size[1]

if image_size > 100000:
    print('Heads up - this program is made specifically for pixel art. Large images are not the best idea...')
print(f'Scanning {file} {"(" + str(image_size) + " pixels, this may take a very very very long time)" if image_size > 10000 else ""}')

for x in range(img.size[0]):
    for y in range(img.size[1]):
        rgb = img.getpixel((x, y))
        if rgb[3] >= 200:
            pixels[1][f'{x},{y}'] = rgb[:3]

def optimize(obj, distance):
    """
    Optimize the given object by scanning each pixel and removing duplicates based on a given distance.
    
    Args:
        obj (dict): A dictionary representing the object, where each key is a string representing the x and y coordinates of a pixel, and the corresponding value is a list representing the color of the pixel.
        distance (int): The distance used to determine duplicates.
        
    Returns:
        dict: A dictionary representing the optimized object, where each key is a string representing the x and y coordinates of a pixel, and the corresponding value is a list representing the color of the pixel.
    """
    scan = True
    updated_obj = {}
    pixels = {}

    for x, col in obj.items():
        if not col or col[3] or not scan:
            continue

        x_coord, y_coord = map(int, x.split(','))
        right_xy = f'{x_coord},{y_coord + distance}'
        down_xy = f'{x_coord + distance},{y_coord}'
        dia_xy = f'{x_coord + distance},{y_coord + distance}'

        right = ' '.join(map(str, obj.get(right_xy, [])))
        down = ' '.join(map(str, obj.get(down_xy, [])))
        dia = ' '.join(map(str, obj.get(dia_xy, [])))

        if ' '.join(map(str, col)) == right == down == dia:
            pixels[distance * 2][x] = col
            del obj[x], obj[right_xy], obj[down_xy], obj[dia_xy]
            scan = False
        else:
            col.append(True)
            updated_obj[x] = col

    print("Updated Object:", updated_obj)
    print("Pixels:", pixels)
    
    return {**updated_obj, **obj}

pixel_count = len(pixels[1])
for i in list(map(int, pixels.keys()))[:-1]:
    print(f'Optimizing image (x{i})')
    while len(pixels[i]) != len(optimize(pixels[i], i)):
        pixels[i] = optimize(pixels[i], i)

def rgb2hsv(r, g, b):
    """
    Convert RGB color values to HSV color space.

    Parameters:
        r (float): The red component of the RGB color (0-255).
        g (float): The green component of the RGB color (0-255).
        b (float): The blue component of the RGB color (0-255).

    Returns:
        list: A list containing the hue, saturation, and value components of the HSV color.
            - hue (int): The hue component of the HSV color (0-359).
            - saturation (float): The saturation component of the HSV color (0-1).
            - value (float): The value component of the HSV color (0-1).
    """
    r, g, b = r / 255, g / 255, b / 255
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn
    
    print(f'r: {r}, g: {g}, b: {b}, mx: {mx}, mn: {mn}, df: {df}')
    
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / df) + 120) % 360
    else:
        h = (60 * ((r - g) / df) + 240) % 360
    
    print(f'h: {h}')
    
    return [round(h), 0 if mx == 0 else df / mx, mx]


print("Converting to GD level...")
levelStr = ""
objCount = 0
for i in pixels:
    for y in pixels[i]:
        pos = list(map(int, y.split(",")))
        xPos = 300 + (pos[0] * 30 / 4) + (i * 3.75)
        yPos = (200 + (img.bitmap.height * 8)) - (pos[1] * 30 / 4) - (i * 3.75)
        hsv = rgb2hsv(*pixels[i][y])
        levelStr += f"1,{tiles[i]},2,{xPos},3,{yPos},21,10,41,1,43,{hsv[0]}a{hsv[1]}a{hsv[2]}a0a0;"
        objCount += 1

import zlib
import base64

with open(gdLevels, 'r') as f:
    saveData = f.read()

if not saveData.startswith('<?xml version="1.0"?>'):
    print("Decrypting GD save file...")

    def xor(string, key):
        res = ""
        for letter in string:
            res += chr(ord(letter) ^ key)
        return res

    saveData = xor(saveData, 11)
    saveData = base64.b64decode(saveData)
    try:
        saveData = zlib.decompress(saveData).decode()
    except Exception as e:
        print("Error! GD save file seems to be corrupt!\nMaybe try saving a GD level in-game to refresh it?\n")

print("Importing to GD...")
saveData = saveData.split("<k>_isArr</k><t />")
saveData[1] = re.sub(r"<k>k_(\d+)<\/k><d><k>kCEK<\/k>", lambda n: "<k>k_" + (int(n.group(1)) + 1) + "</k><d><k>kCEK</k>", saveData[1])
saveData = saveData[0] + "<k>_isArr</k><t />" + data.ham + data.bur + levelStr + data.ger + saveData[1]
saveData = saveData.replace("[[NAME]]", file.split(".")[0].replace(r"[^a-z|0-9]", "")[:30]).replace("[[DESC]]", f"{file} | {objCount} objects")

with open(gdLevels, 'w') as f:
    f.write(saveData)

print(f"Saved! ({objCount} objects)")