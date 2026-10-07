# Leeds 053: export LOD1 open-data BIM (IFC4) – one IfcBuilding per plot footprint, extruded to eaves height,
# georeferenced to EPSG:27700 via IfcMapConversion; geometry + EPC attributes as property sets.
import os,shutil,time,numpy as np,geopandas as gpd,ifcopenshell,ifcopenshell.api as api,ifcopenshell.guid as guid
D=(__import__("paths").ROOT+"")
fp=gpd.read_file(D+"02_processed/v4_district/l053_buildings_v2.gpkg")
fp=fp[fp.height_m.notna()].reset_index(drop=True)
X0,Y0=np.floor(fp.total_bounds[:2])
f=ifcopenshell.file(schema="IFC4")
proj=api.run("root.create_entity",f,ifc_class="IfcProject",name="Paper4 – Leeds 053 open-data BIM (LOD1)")
L=api.run("unit.add_si_unit",f,unit_type="LENGTHUNIT"); A=api.run("unit.add_si_unit",f,unit_type="AREAUNIT"); V=api.run("unit.add_si_unit",f,unit_type="VOLUMEUNIT"); api.run("unit.assign_unit",f,units=[L,A,V])
ctx=api.run("context.add_context",f,context_type="Model")
body=api.run("context.add_context",f,context_type="Model",context_identifier="Body",target_view="MODEL_VIEW",parent=ctx)
crs=f.createIfcProjectedCRS(Name="EPSG:27700",Description="OSGB36 / British National Grid",GeodeticDatum="OSGB36",MapProjection="Transverse Mercator")
f.createIfcMapConversion(SourceCRS=ctx,TargetCRS=crs,Eastings=float(X0),Northings=float(Y0),OrthogonalHeight=0.0)
site=api.run("root.create_entity",f,ifc_class="IfcSite",name="Leeds 053 (MSOA E02002382), Harehills, Leeds")
api.run("aggregate.assign_object",f,relating_object=proj,products=[site])
def prop(pset,d): api.run("pset.edit_pset",f,pset=pset,properties={k:(None if v is None or (isinstance(v,float) and np.isnan(v)) else (v.item() if hasattr(v,"item") else v)) for k,v in d.items()})
origin=f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.,0.,0.)))
t=time.time()
for i,r in fp.iterrows():
    g=r.geometry; g=max(g.geoms,key=lambda p:p.area) if g.geom_type=="MultiPolygon" else g
    xy=[(float(x-X0),float(y-Y0)) for x,y,*_ in g.exterior.coords][:-1]
    z0=float(r.ground_m) if r.ground_m==r.ground_m else 0.0; hgt=float(r.eaves_m)
    b=api.run("root.create_entity",f,ifc_class="IfcBuilding",name=f"L053-{int(r.bid):05d}")
    api.run("aggregate.assign_object",f,relating_object=site,products=[b])
    el=api.run("root.create_entity",f,ifc_class="IfcBuildingElementProxy",name=f"L053-{int(r.bid):05d} LOD1 body")
    api.run("spatial.assign_container",f,relating_structure=b,products=[el])
    pl=f.createIfcLocalPlacement(None,f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.,0.,z0))))
    el.ObjectPlacement=pl; b.ObjectPlacement=pl
    prof=f.createIfcArbitraryClosedProfileDef("AREA",None,f.createIfcPolyline([f.createIfcCartesianPoint(p) for p in xy+[xy[0]]]))
    solid=f.createIfcExtrudedAreaSolid(prof,origin,f.createIfcDirection((0.,0.,1.)),hgt)
    el.Representation=f.createIfcProductDefinitionShape(None,None,[f.createIfcShapeRepresentation(body,"Body","SweptSolid",[solid])])
    ps=api.run("pset.add_pset",f,product=b,name="Pset_Paper4_Geometry")
    prop(ps,dict(FootprintArea=r.area_m2,Perimeter=r.perim_m,RidgeHeight=r.height_m,EavesHeight=r.eaves_m,RoofPitch=r.roof_pitch_deg,
        PartyWallLength=r.party_wall_len_m,ExposedPerimeter=r.exposed_perim_m,ExposedWallArea=r.exposed_wall_m2,PartyWallArea=r.party_wall_m2,
        RoofArea=r.roof_area_m2,PVSuitableRoofArea=r.pv_area_m2,HeatLossArea=r.heat_loss_area_m2,FormFactor=r.form_factor,
        GroundElevation=r.ground_m,LidarValid=bool(r.lidar_ok),Source="INSPIRE parcels ∩ OS Open Map Local; EA composite DSM 1m/DTM 2m 2022"))
    ps2=api.run("pset.add_pset",f,product=b,name="Pset_Paper4_EPC")
    prop(ps2,dict(EPCDwellings=int(r.n_epc),EPCFloorArea=r.epc_tfa_m2,FloorArea=r.floor_area_m2,FloorAreaSource=r.floor_area_src,
        BuiltForm=r.built_form,PropertyType=r.prop_type,EPCBand=r.epc_band,AgeBand=None if r.age_band!=r.age_band else str(r.age_band),
        EPCPrimaryEnergy=r.epc_kwh_m2,PredictedGas_kWh=r.pred_gas_kwh,PredictedElec_kWh=r.pred_elec_kwh,Postcode=r.postcode))
out=(__import__("paths").WORK+"Leeds053_LOD1.ifc"); f.write(out)
shutil.copy(out,D+"03_outputs/v4_district/Leeds053_LOD1.ifc")
print("buildings",len(fp),"secs",round(time.time()-t),"MB",round(os.path.getsize(out)/1e6,1),"origin",X0,Y0)
