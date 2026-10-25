"""New authored V2 prism probes, independent rational volume oracle; NOT a holdout or model evaluation."""
import copy
import hashlib
import json
import sys
from fractions import Fraction as F
from math import isqrt
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "backend/app").is_dir())
sys.path.insert(0, str(ROOT / "backend"))
from app.ai.adapter4_route import run_typed_fact_next_v2_route, build_adapter4_response
from app.simulation.geometry_functions.typed_fact_next import parse_typed_fact_next_v2

def case(labels="ABC", x=6, y=8, h=12, oblique=False):
    a,b,c=labels
    base=list(labels); top=[v+"'" for v in base]
    name=labels+"."+"".join(top)
    solid=f"Cho lăng trụ {'đứng ' if not oblique else ''}{name}."
    shape=f"Đáy {labels} là tam giác vuông tại {a}."
    qs=[solid,shape,f"{a}{b} = {x}.",f"{a}{c} = {y}."]
    premises=[{"kind":"right_angle","args":{"vertex":a,"rays":[b,c]},"quote":shape},
              *[{"kind":"segment_length","args":{"segment":seg,"value":str(v)},"quote":q}
                for seg,v,q in (([a,b],x,qs[2]),([a,c],y,qs[3]))]]
    if oblique:
        q1=f"Gọi H là trung điểm của {b}{c}."
        q2=f"Hình chiếu vuông góc của {a}' lên ({labels}) là H."
        # Families chosen so sqrt(h²+(x²+y²)/4) is rational and stated exactly.
        l2=F(h*h)+F(x*x+y*y,4)
        l=isqrt(l2.numerator)//isqrt(l2.denominator); assert l*l==l2
        q3=f"{a}{a}' = {l}."
        premises += [{"kind":"midpoint","args":{"point":"H","segment":[b,c]},"quote":q1},
                     {"kind":"orthogonal_projection","args":{"point":a+"'","image":"H","plane":base},"quote":q2},
                     {"kind":"segment_length","args":{"segment":[a,a+"'"],"value":str(l)},"quote":q3}]
        qs += [q1,q2,q3]
    else:
        q=f"{a}{a}' = {h}."; qs.append(q)
        premises += [{"kind":"right_prism","args":{"base":base,"top":top},"quote":solid},
                     {"kind":"segment_length","args":{"segment":[a,a+"'"],"value":str(h)},"quote":q}]
    ask=f"Tính thể tích khối lăng trụ {name}."; qs.append(ask)
    return {"schema_version":"typed-fact-next/2","problem_text":" ".join(qs),"length_unit":"1",
            "solids":[{"solid_id":"pr","solid_type":"prism","notation":name,"quote":solid}],
            "premises":premises,"simulation_goals":[{"goal_id":"draw","kind":"construct_object","target_solid_id":"pr","quote":solid}],
            "math_goals":[{"goal_id":"q","kind":"measurement","goal_type":"volume","target":{"solid":"pr"},"quote":ask}]},F(x*y*h,2)

rows=[]
for labels,x,y,h,oblique in [("ABC",6,8,12,False),("DEF",6,8,12,False),("KLM",10,24,84,False),
                            ("RST",12,16,24,False),("ABC",6,8,12,True),("DEF",6,8,12,True),("KLM",12,16,24,True)]:
    p,expected=case(labels,x,y,h,oblique)
    r=run_typed_fact_next_v2_route(p)
    row={"kind":"oblique" if oblique else "right", "labels":labels,"dimensions":[x,y,h],"expected_volume":str(expected),
         "source_sha256":hashlib.sha256(p["problem_text"].encode()).hexdigest(),"status":r.status,"code":r.code}
    if r.status=="SERVED":
        v=r.exec_result.final_memory["kq_q"]
        actual2=F(v.he)**2*v.can if hasattr(v,"can") else F(v)**2
        row["exact_oracle_match"]=actual2==expected**2
        pairs=zip(labels,[v+"'" for v in labels]); vectors=[tuple(r.points[t][i]-r.points[b][i] for i in range(3)) for b,t in pairs]
        row["one_lateral_vector"]=len(set(vectors))==1
        row["adapter4_status"]=build_adapter4_response(r,p["problem_text"])["route_d"]["status"]
        assert row["exact_oracle_match"] and row["one_lateral_vector"]
    rows.append(row)
for kind in ('missing_height','missing_base_angle','zero_height','contradictory_height','invented_rightness'):
    p,_=case()
    if kind in ('missing_height','missing_base_angle'):
        matches=lambda x: (x['kind']=='segment_length' and x['args']['segment']==['A',"A'"]) if kind=='missing_height' else x['kind']=='right_angle'
        removed=[x for x in p['premises'] if matches(x)]
        p['premises']=[x for x in p['premises'] if not matches(x)]
        for x in removed:p['problem_text']=p['problem_text'].replace(x['quote'],'')
    elif kind=='zero_height':
        p['problem_text']=p['problem_text'].replace("AA' = 12.","AA' = 0.")
        x=next(x for x in p['premises'] if x['kind']=='segment_length' and x['args']['segment']==['A',"A'"])
        x['args']['value']='0';x['quote']="AA' = 0."
    elif kind=='contradictory_height':
        q="AA' = 13.";p['problem_text']+=' '+q
        p['premises'].append({'kind':'segment_length','args':{'segment':['A',"A'"],'value':'13'},'quote':q})
    else:
        p['problem_text']=p['problem_text'].replace('lăng trụ đứng','lăng trụ')
        p['solids'][0]['quote']=p['solids'][0]['quote'].replace('lăng trụ đứng','lăng trụ')
        for x in p['premises']:x['quote']=x['quote'].replace('lăng trụ đứng','lăng trụ')
    r=run_typed_fact_next_v2_route(p)
    assert r.status=='REFUSED',(kind,r.status,r.code)
    rows.append({'kind':kind,'status':r.status,'code':r.code,'source_sha256':hashlib.sha256(p['problem_text'].encode()).hexdigest()})
for kind in ("sphere","cone","cylinder"):
    q={"sphere":"Cho mặt cầu tâm O bán kính 5.","cone":"Cho hình nón tâm đáy O đỉnh S bán kính 5 chiều cao 12.",
       "cylinder":"Cho hình trụ tâm đáy O và I bán kính 5 chiều cao 12."}[kind]
    p={"schema_version":"typed-fact-next/2","problem_text":q,"solids":[{"solid_id":"s","solid_type":kind,
       "notation":"(S)","center":"O","radius":"5","quote":q}],
       "simulation_goals":[{"goal_id":"draw","kind":"construct_object","target_solid_id":"s","quote":q}]}
    parse_typed_fact_next_v2(p)
    r=run_typed_fact_next_v2_route(p)
    assert r.status=="REFUSED" and r.code=="BRIDGE_UNSUPPORTED_CURVED"
    rows.append({"kind":kind,"schema":"VALID","status":r.status,"code":r.code})
out={"classification":"OFFLINE_AUTHORED_NEW_PROBES_NOT_HOLDOUT_NOT_NLU","provider_calls":0,"rows":rows}
output = Path(sys.argv[1]) if len(sys.argv)>1 else Path(__import__("tempfile").mkdtemp(prefix="algosim-capability-"))/"receipt.json"
if output.exists():
    raise FileExistsError("Fresh replay output required; never overwrite evidence")
output.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,indent=2))
