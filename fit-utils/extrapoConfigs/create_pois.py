import json 
pois=['ctlSi', 'ctZ', 'ctq1', 'ctq8', 'ctei', 'cpQM', 'ctW', 'ctG', 'ctli', 'ctlTi', 'cQl3i', 'cQq83', 'ctt1', 'cbW', 'cQei', 'cQQ1', 'ctp', 'cpt', 'cQlMi', 'cQq11', 'cpQ3', 'cQt1', 'cptb', 'cQq13', 'cQq81', 'cQt8']

stuff={}
for p in pois:
    stuff[p]= { 'range' : [-20,20], 'val' : 0}

dump=json.dumps( stuff, indent=4 )
outf=open("extrapoConfigs/full_pois.json",'w')
outf.write(dump)
outf.close()
