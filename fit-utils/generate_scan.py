import json
import numpy as np 

stuff=json.loads(open( "../extrapoConfigs/full_pois.json").read())
pois=[p for p in stuff]
import csv


def get_pois_val_list(poi_val_dict):
    ret=[0 for x in pois]
    for p in poi_val_dict:
        ret[pois.index(p)]=poi_val_dict[p]
    return ret
npoints=5000
with open('scan.csv', 'w', newline='') as csvfile:
    scanwriter = csv.writer(csvfile, delimiter=',')
    scanwriter.writerow(pois)
    scanwriter.writerow(get_pois_val_list( {} )) # all zeros
    for i in range(npoints):
        values=[]
        for i1,p in enumerate(pois):
            ranges=stuff[p]['range']
            values.append( np.random.normal(loc=0, scale=ranges[1]/100.) )
        
        scanwriter.writerow( values )
