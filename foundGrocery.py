import json

while True:
    fp = open('/home/pi/VisionX/allobject.json', 'r')
    data = json.load(fp)
    fp.close()

    fp2 = open('/home/pi/VisionX/groceryList.txt', 'r')
    lines = fp2.readlines()
    fp2.close()


    objects = []
    for i in range(len(data['objects'])):
        objects.append(data['objects'][i]['name'])

    fp3 = open('/home/pi/VisionX/foundGrocery.txt', 'w')
    for i in lines:
        if i.strip() in objects:
            fp3.write(i.strip() + '\n')

    fp3.close()
