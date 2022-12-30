f = open("network_combined.csv", 'r')

next(f) #sert a sauter une ligne
for line in f:
    items = line.rstrip("\n").split(";")
    b= items[5].split(",")
    for part in b:
        c = part.split(":")
        print(f"INSERT INTO combined_projet VALUES ( \'{items[0]}\',\'{items[1]}\',\'{items[2]}\',\'{items[3]}\',\'{items[4]}\',\'{c[0]}\',\'{items[6]}\');")

