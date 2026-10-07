"""RQ3 reduced-input transfer models on NEED (England excl. Y&H). Usage: 21_train_tier_models.py T2|T3|T4"""
import sys, pandas as pd, lightgbm as lgb, json
tier=sys.argv[1]
FEAT={"T2":["PROP_TYPE","FLOOR_AREA_BAND","MAIN_HEAT_FUEL"],"T3":["PROP_TYPE","MAIN_HEAT_FUEL"],"T4":["IMD_BAND_ENG"]}[tier]
CATS={"PROP_TYPE":["Detached","Semi detached","Mid terrace","End terrace","Bungalow","Flat"]}
d=pd.read_parquet("02_processed/need2026_england_slim.parquet",columns=list(set(FEAT+["MAIN_HEAT_FUEL","REGION","EPC","Gcons2024","GasValFlag2024","Econs2024","ElecValFlag2024"])))
d=d[(d.REGION.astype(str)!="E12000003")&(d.EPC.astype(str)!="No EPC")]
def prep(x):
    x=x[FEAT].copy()
    for c in FEAT: x[c]=pd.Categorical(x[c].astype(str),categories=CATS[c]) if c in CATS else x[c].astype(float)
    return x
out={}
for fuel,(y,f) in {"gas":("Gcons2024","GasValFlag2024"),"elec":("Econs2024","ElecValFlag2024")}.items():
    t=d[(d[f]=="V")]
    if fuel=="gas": t=t[t.MAIN_HEAT_FUEL==1]
    t=t.dropna(subset=FEAT+[y]).sample(n=min(len(t),800_000),random_state=7)
    m=lgb.train(dict(objective="regression",learning_rate=0.05,num_leaves=31,min_data_in_leaf=200,verbose=-1,num_threads=2,seed=7),
                lgb.Dataset(prep(t),t[y],categorical_feature=[c for c in FEAT if c in CATS]),num_boost_round=200)
    m.save_model(f"models/need_{tier}_{fuel}.txt"); out[fuel]=len(t)
print(tier,FEAT,out)
