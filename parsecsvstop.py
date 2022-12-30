f = open("network_nodes.csv", 'r')

next(f) #sert a sauter une ligne
for line in f:
    items = line.rstrip("\n").split(";")
    print(f"INSERT INTO stations VALUES ( \'{items[0]}\'", end='')
    for item in items[1:] :
        item = item.replace("'", "''")
        if(item != ''):
            print(f", \'{item}\'" ,end='')

    print(");")