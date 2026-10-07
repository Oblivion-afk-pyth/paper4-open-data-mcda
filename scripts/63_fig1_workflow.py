"""Fig. 1 (v0.8): two-stage workflow – city stage (LSOAs, Leeds and Bradford) and district stage (Leeds 053, open-data BIM)."""
import os,matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,Rectangle
from matplotlib import font_manager as fm
fam="Liberation Sans" if any("Liberation Sans" in f.name for f in fm.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams["font.family"]=fam; plt.rcParams["mathtext.fontset"]="custom"; plt.rcParams["mathtext.rm"]=fam; plt.rcParams["mathtext.it"]=fam+":italic"
INK="#1f2937"; INK2="#374151"; EDGE="#4a5568"; OR="#c8662b"; ORF="#fde8d9"; ARR="#4a5568"
BAND=["#e9eff6","#f1f2ee"]; DBAND="#e8f1e4"; DHEAD="#cfe3c6"; GREEN="#3f7d3a"
W=110; H=139
fig=plt.figure(figsize=(11,H/10)); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(H,0); ax.axis("off")
def band(y,h,color,title,sub):
    ax.add_patch(Rectangle((1,y),108,h,facecolor=color,edgecolor="none",zorder=0))
    k=sub.count("\n"); dy=1.0+0.65*max(0,k-1)
    ax.text(2.2,y+h/2-dy,title,fontsize=9.5,fontweight="bold",color=INK,va="center")
    ax.text(2.2,y+h/2-dy+1.6,sub,fontsize=8,color=INK2,va="top",linespacing=1.25)
def box(x,y,w,h,title,body="",kind="n",fs=7.6):
    if body.count("\n")>=2: y=y-0.45; h=max(h,7.9)
    fc={"n":"white","o":ORF,"d":"white","ob":"white","g":"white","res":"#e6edf7"}[kind]; ec={"n":EDGE,"o":OR,"d":"#8a94a6","ob":OR,"g":GREEN,"res":"#1e3a5f"}[kind]
    ls="--" if kind=="d" else "-"; lw=1.6 if kind=="res" else 1.0
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0,rounding_size=0.8",facecolor=fc,edgecolor=ec,lw=lw,ls=ls,zorder=2))
    ty=(y+1.7) if body.count("\n")>=2 else y+h/2-(1.2 if body else 0)
    ax.text(x+w/2,ty,title,ha="center",va="center",fontsize=fs+0.4,fontweight="bold",color=INK,zorder=3)
    if body: ax.text(x+w/2,ty+1.25,body,ha="center",va="top",fontsize=fs,color=INK2,linespacing=1.3,zorder=3,style="italic" if kind=="d" else "normal")
    return (x,y,w,h)
def arrow(p,q,color=ARR,ls="-",lw=1.0):
    ax.annotate("",xy=q,xytext=p,arrowprops=dict(arrowstyle="-|>",color=color,lw=lw,ls=ls,shrinkA=0,shrinkB=0,mutation_scale=9),zorder=1)
def line(pts,color=ARR,ls="-",lw=1.0,end=True):
    xs,ys=zip(*pts); ax.plot(xs[:-1] if end else xs,ys[:-1] if end else ys,color=color,ls=ls,lw=lw,zorder=1) if False else None
    for a,b in zip(pts[:-2],pts[1:-1]): ax.plot([a[0],b[0]],[a[1],b[1]],color=color,ls=ls,lw=lw,zorder=1)
    if end: arrow(pts[-2],pts[-1],color,ls,lw)
    else: ax.plot([pts[-2][0],pts[-1][0]],[pts[-2][1],pts[-1][1]],color=color,ls=ls,lw=lw,zorder=1)
bot=lambda b:(b[0]+b[2]/2,b[1]+b[3]); top=lambda b:(b[0]+b[2]/2,b[1]); rgt=lambda b:(b[0]+b[2],b[1]+b[3]/2); lft=lambda b:(b[0],b[1]+b[3]/2)
RH=10; G=0.8; Y=[4.5+i*(RH+G) for i in range(8)]
ax.text(13,2.6,"CITY STAGE – which neighbourhoods? (Leeds, 488 LSOAs; Bradford holdout, 312 LSOAs)",fontsize=9,fontweight="bold",color="#1e3a5f",va="center")
ax.text(98,2.6,"Meter-informed reference",fontsize=8,color=OR,style="italic",ha="center",va="center")
# P1
band(Y[0],RH,BAND[0],"Phase 1","Open-data\nacquisition")
xs=[13,25,37,49,61]; T=[("EPC register","Leeds + Yorkshire,\nlodged 2008–2024"),("NEED 2026","4M records with\nmetered use"),("Census 2021","household size,\ntenure, occupancy"),("IoD 2025 +","fuel poverty (LILEE)\nper LSOA"),("ONS lookup","postcode → LSOA,\n2021 boundaries")]
b1=[box(x,Y[0]+1.2,11,7,t,s) for x,(t,s) in zip(xs,T)]
bcal=box(73,Y[0]+1.2,11,7,"Meters, other","Yorkshire LSOAs\ncalibration only","d")
bmet=box(87,Y[0]+1.2,21,7,"Leeds metered data","DESNZ LSOA and postcode\ngas + electricity, 2024\nreference only","o")
# P2
band(Y[1],RH,BAND[1],"Phase 2","Pre-processing\nand harmonisation")
b2=[box(13,Y[1]+1.5,22,7,"Latest EPC ≤ 2024","de-duplicated by UPRN\n(269,532 Leeds dwellings)"),box(39,Y[1]+1.5,22,7,"Link to neighbourhoods","postcode → 2021 LSOA\n(266,549 in 488 LSOAs)"),box(65,Y[1]+1.5,22,7,"Harmonise EPC → NEED","type, age, floor area,\nrating, fuel, PV, IMD")]
yy=Y[0]+RH-0.3; ax.plot([b1[0][0]+5.5,b1[-1][0]+5.5],[yy,yy],color=ARR,lw=1)
for b in b1: ax.plot([b[0]+5.5]*2,[b[1]+b[3],yy],color=ARR,lw=1)
arrow((24,yy),top(b2[0])); arrow(rgt(b2[0]),lft(b2[1])); arrow(rgt(b2[1]),lft(b2[2]))
# P3
band(Y[2],RH,BAND[0],"Phase 3","Transfer machine\nlearning (RQ1)")
b3=[box(13,Y[2]+1.5,22,7,"Train LightGBM on NEED","gas + electricity models,\n8 regions outside Yorkshire"),box(39,Y[2]+1.5,22,7,"Test on unseen region","Yorkshire and The Humber;\nR² of group means 0.98 / 0.93"),box(65,Y[2]+1.5,22,7,"Predict Leeds dwellings","aggregate to 488 LSOAs\n= proxy T1")]
m=Y[2]-G/2-0.0; line([bot(b2[2]),(76,Y[1]+RH+0.4),(24,Y[1]+RH+0.4),top(b3[0])]); arrow(rgt(b3[0]),lft(b3[1])); arrow(rgt(b3[1]),lft(b3[2]))
# P4
band(Y[3],RH,BAND[1],"Phase 4","Area-level\ncorrection")
b4=[box(39,Y[3]+1.5,22,7,"Learn correction","ln(metered / proxy); 16 features;\n2,868 LSOAs, 14 other LAs"),box(65,Y[3]+1.5,22,7,"Apply to Leeds","proxy × exp(ŷ)\n= corrected proxy T1c")]
arrow(bot(b3[1]),top(b4[0])); arrow(bot(b3[2]),top(b4[1])); arrow(rgt(b4[0]),lft(b4[1]))
line([bot(bcal),(78.5,Y[1]-0.4),(88.5,Y[1]-0.4),(88.5,Y[3]-0.4),(36,Y[3]-0.4),(36,Y[3]+5),lft(b4[0])],color="#8a94a6",ls="--")
# P5
band(Y[4],RH,BAND[0],"Phase 5","Decision matrices\n(LSOAs × 6 criteria)")
bc=box(13,Y[4]+0.8,95,3.6,"C1 energy intensity · C2 carbon abatement · C3 fuel poverty · C4 income deprivation · C5 cost-effectiveness · C6 stock homogeneity",fs=7.4)
bxp=box(57,Y[4]+5.4,22,4,"Proxy matrix $X_P$","C1, C2, C5 from T1c or T1"); bxm=box(84,Y[4]+5.4,24,4,"Reference matrix $X_M$","C1, C2, C5 from meters","o")
ax.text(14,Y[4]+7.3,"Same criteria and method;\nonly energy inputs differ",fontsize=7.6,style="italic",color=INK2,va="center")
arrow(bot(b4[1]),(76,bc[1])); arrow((68,Y[4]+4.4),top(bxp)); arrow((96,Y[4]+4.4),top(bxm))
# P6
band(Y[5],RH,BAND[1],"Phase 6","Data-driven\nweighting and\nranking")
bw=box(13,Y[5]+1.5,22,7,"Weights fixed from $X_P$","entropy × CRITIC; equal;\nenergy-heavy 70% / 90%"); bg=box(39,Y[5]+1.5,24,7,"Grey relational analysis","ξ = 0.5\nchecks: TOPSIS, VIKOR"); brp=box(67,Y[5]+2.5,15,5,"Proxy ranking $R_P$"); brm=box(88,Y[5]+2.5,20,5,"Reference ranking $R_M$",kind="o")
line([bot(bxp),(68,Y[5]-0.4),(24,Y[5]-0.4),top(bw)]); arrow(rgt(bw),lft(bg)); arrow(rgt(bg),lft(brp)); arrow(bot(bxm),top(brm))
# P7
band(Y[6],RH,BAND[0],"Phase 7","Validation")
bdv=box(39,Y[6]+1.5,43,7,"Decision validation (RQ2)","$R_P$ vs $R_M$: ρ, τ, top-20% overlap, rank shift;\nMSOA-cluster bootstrap CIs; threshold grid"); bpv=box(86,Y[6]+1.5,22,7,"Prediction validation (RQ1)","T1, T1c vs meters: MAPE,\nR², bias, ρ; Bradford holdout","ob")
line([bot(brp),(74.5,Y[6]-0.4),(60.5,Y[6]-0.4),top(bdv)]); line([bot(brm),(98,Y[6]-0.4),(62,Y[6]-0.4),(62,Y[6]+1.5)])
line([(106,bmet[1]+bmet[3]),(106,Y[4]+5.4-0.1)],color=OR,ls="--"); arrow((106,Y[4]+9.6),(106,Y[6]+1.5),color=OR,ls="--")
arrow((92,Y[0]+8.2),(92,Y[4]+0.8),color=OR,ls="--")
# P8
band(Y[7],RH,BAND[1],"Phase 8","Robustness and\ndiagnosis")
b8=[box(13,Y[7]+1.5,29,7,"Data-reduction tiers","T1c → T1 → T2 → T3 → T4\n(supplementary analysis)"),box(46,Y[7]+1.5,29,7,"Robustness (RQ4)","Monte Carlo: uniform, empirical,\nspatially correlated errors"),box(79,Y[7]+1.5,29,7,"Misplacement (RQ4)","Moran's I; OLS and\nspatial error model")]
yy=Y[7]-0.4; ax.plot([27.5,93.5],[yy,yy],color=ARR,lw=1); ax.plot([60.5,60.5],[Y[6]+8.5,yy],color=ARR,lw=1)
for b in b8: arrow((b[0]+b[2]/2,yy),top(b))
# DISTRICT
yd=Y[7]+RH+2.2
ax.add_patch(Rectangle((1,yd),108,4.6,facecolor=DHEAD,edgecolor="none",zorder=0))
ax.text(13,yd+2.3,"DISTRICT STAGE – which postcodes and buildings? (Leeds 053, Harehills: 81 postcodes, 2,711 buildings)",fontsize=9,fontweight="bold",color=GREEN,va="center")
arrow((60.5,Y[7]+8.5),(60.5,yd),color=GREEN,lw=1.4); ax.text(62,yd-1.2,"top-ranked district: 4 of the 5 highest-priority LSOAs",fontsize=7.4,style="italic",color=GREEN,va="center")
YD=[yd+5.4+i*(RH+G) for i in range(3)]
band(YD[0],RH,DBAND,"Phase 9","Open-data\nBIM layer")
b9=[box(13,YD[0]+1.5,21.5,7,"Footprint subdivision","INSPIRE parcels ∩\nOS Open Map Local\n(230 blocks → 2,727 plots)","g"),box(37.5,YD[0]+1.5,21.5,7,"Heights and roofs","EA DSM 1 m − DTM 2 m:\nridge, eaves, pitch, aspect","g"),box(62,YD[0]+1.5,21.5,7,"Geometry and linkage","party walls, exposed wall,\nform factor, PV roof;\nEPC via UPRN","g"),box(86.5,YD[0]+1.5,21.5,7,"IFC4 export","LOD1, EPSG:27700;\ngeometry, EPC and\npriority property sets","g")]
for a,b in zip(b9[:-1],b9[1:]): arrow(rgt(a),lft(b))
band(YD[1],RH,DBAND,"Phase 10","Postcode\ndecision matrices")
bpc=box(13,YD[1]+1.5,29,7,"Postcode criteria","C1–C6 as city stage (T1c)\n+ C7 form factor, C8 PV roof area\n(median dwelling, winsorised)","g")
bxp2=box(46,YD[1]+1.5,17,7,"Proxy matrix $X_P$","energy from\nT1c predictions"); bgr2=box(67,YD[1]+1.5,17,7,"GRA, fixed weights","$R_P$ vs $R_M$;\nsix vs eight criteria"); bxm2=box(88,YD[1]+1.5,20,7,"Reference matrix $X_M$","energy from\npostcode meters (2024)","o")
line([bot(b9[2]),(72.75,YD[1]-0.4),(27.5,YD[1]-0.4),top(bpc)]); arrow(rgt(bpc),lft(bxp2)); arrow(rgt(bxp2),lft(bgr2)); arrow(lft(bxm2),rgt(bgr2))
line([(106,bpv[1]+bpv[3]),(106,Y[6]+RH+0.4),(108.6,Y[6]+RH+0.4),(108.6,YD[1]-0.4),(104,YD[1]-0.4),(104,YD[1]+1.5)],color=OR,ls="--")
band(YD[2],RH,DBAND,"Phase 11","District validation\nand robustness")
b11=[box(13,YD[2]+1.5,21.5,7,"Prediction (RQ1)","postcode MAPE, R², ρ;\nnoise ceiling from NEED\nhousehold variance","ob"),box(37.5,YD[2]+1.5,21.5,7,"Decision (RQ2)","ρ, top-20% overlap,\nbootstrap CIs; energy-\ncriteria-only test","g"),box(62,YD[2]+1.5,21.5,7,"BIM contribution (RQ3)","form factor vs metered\nintensity (partial ρ);\nsix vs eight criteria","g"),box(86.5,YD[2]+1.5,21.5,7,"Robustness (RQ4)","TOPSIS, VIKOR; Monte Carlo\nfrom out-of-district residuals;\nMoran's I; building scores","g")]
yy=YD[2]-0.4; ax.plot([23.75,97.25],[yy,yy],color=ARR,lw=1); ax.plot([75.5,75.5],[YD[1]+8.5,yy],color=ARR,lw=1)
for b in b11: arrow((b[0]+b[2]/2,yy),top(b))
yr=YD[2]+RH+G
ax.text(2.2,yr+4,"Results",fontsize=9.5,fontweight="bold",color=INK,va="center")
br=box(13,yr+0.6,95,7,"Outputs","city neighbourhood ranking and data-collection guidance (Leeds, Bradford) · district postcode and building priorities\nrobust priority cores at both scales · IFC model with priority property sets for renovation design","res")
for b in b11: arrow(bot(b),(b[0]+b[2]/2,yr+0.6))
ax.set_ylim(yr+8.5,0); fig.set_size_inches(11,(yr+8.5)/10)
OUT=(__import__("paths").ROOT+"03_outputs/v4_district/figures/")
fig.savefig(OUT+"Fig1_workflow_v08.png",dpi=300); fig.savefig(OUT+"Fig1_workflow_v08.pdf"); print(fam,"saved")
