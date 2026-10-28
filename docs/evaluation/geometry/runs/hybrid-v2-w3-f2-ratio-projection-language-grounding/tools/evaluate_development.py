"""Preregister and evaluate F2 with the existing independent oracle and scorer (offline)."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
HIST = ROOT / 'docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3'
F1 = ROOT / 'docs/evaluation/geometry/runs/hybrid-v2-w3-f1-cross-sentence-plane-grounding'
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(HIST / 'tools'))
os.environ['ALLOW_LIVE_AI'] = '0'
sys.dont_write_bytecode = True


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def oracle_module():
    spec = importlib.util.spec_from_file_location('f2_independent_oracle', HIST / 'oracle/oracle_holdout_wave3.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_quote(case, old, new):
    p = case['payload']
    assert old in p['problem_text'], old
    def visit(value):
        if isinstance(value, dict):
            return {k: visit(v) for k, v in value.items()}
        if isinstance(value, list):
            return [visit(v) for v in value]
        return new if value == old else value
    text = p['problem_text'].replace(old, new)
    case['payload'] = visit(p)
    case['payload']['problem_text'] = case['problem_text'] = text


def canonical_f2(case):
    c = deepcopy(case)
    for prem in list(c['payload']['premises']):
        a = prem['args']
        if prem['kind'] == 'divide_segment':
            x, y = a['segment']
            new = f"Gọi {a['point']} là điểm thuộc cạnh {x}{y} sao cho {x}{a['point']} = {a['ratio']} {x}{y}"
        elif prem['kind'] == 'orthogonal_projection':
            new = f"Hình chiếu vuông góc của {a['point']} lên mặt phẳng ({''.join(a['plane'])}) là {a['image']}"
        else:
            continue
        replace_quote(c, prem['quote'], new)
    return c


def refresh_points(case, geom, independent):
    points = {**geom['solid_vertices'], **geom.get('named_points', {})}
    named = geom.setdefault('named_points', {})
    for prem in case['payload']['premises']:
        a = prem['args']
        if prem['kind'] not in ('divide_segment', 'midpoint'):
            continue
        u, v = (list(map(F, points[n])) for n in a['segment'])
        t = F(a['ratio']) if prem['kind'] == 'divide_segment' else F(1, 2)
        points[a['point']] = named[a['point']] = [str(x + t * (y - x)) for x, y in zip(u, v)]
    vertices = {k: tuple(map(F, v)) for k, v in geom['solid_vertices'].items()}
    np = {k: tuple(map(F, v)) for k, v in named.items()}
    n, d = independent._plane_normal_and_d(case['id'], geom['plane'], vertices, np)
    for st in case['payload']['derived_sections'][0].get('stated_intersections', []):
        u, v = (vertices[k] for k in st['edge'])
        t = (d - sum(x * y for x, y in zip(n, u))) / sum(x * (z - y) for x, y, z in zip(n, u, v))
        named[st['point']] = [str(x + t * (y - x)) for x, y in zip(u, v)]


def rename(value, mapping):
    def text(s):
        return re.sub(r"(?<!\w)[A-Z][A-Z0-9']*(?!\w)",
                      lambda m: re.sub(r"[A-Z][0-9]*'?", lambda n: mapping.get(n[0], n[0]), m[0]), s)
    if isinstance(value, dict):
        return {text(k): rename(v, mapping) for k, v in value.items()}
    if isinstance(value, list):
        return [rename(v, mapping) for v in value]
    return text(value) if isinstance(value, str) else value


def authored(source, geometry, index, group, style, independent):
    c = canonical_f2(source)
    g = deepcopy(geometry)
    # Different labels, dimensions and exact ratio; these are authored/metamorphic DEV, never blind data.
    labels = sorted(set(g['solid_vertices']) | set(g.get('named_points', {})))
    bases = sorted(set(x.rstrip("'") for x in labels))
    rotated = 'UVWXYZABCDEFGHIJKLMNOPQRST'
    mapping = {x: rotated[(i + index) % 26] for i, x in enumerate(bases)}
    mapping.update({x + "'": y + "'" for x, y in list(mapping.items())})
    c['payload'] = rename(c['payload'], mapping)
    g = rename(g, mapping)
    c['problem_text'] = c['payload']['problem_text']
    c['id'] = f'DEV-{group.upper()}-{index:02d}'
    c['slice'] = f'authored_{group}'
    c['development_origin'] = source['id']
    c['variation'] = style
    c.pop('known_independent_limit', None)
    p = c['payload']
    # Plane symbols are separate from source vertex labels.
    sec = p['derived_sections'][0]
    old_plane = sec['plane_name']
    p['problem_text'] = p['problem_text'].replace(f'({old_plane})', '(β)')
    for obj in [*p['derived_sections'], *p['simulation_goals'], *p['math_goals']]:
        obj['quote'] = obj['quote'].replace(f'({old_plane})', '(β)')
    sec['plane_name'] = 'β'
    for prem in list(p['premises']):
        a = prem['args']
        key = 'value' if prem['kind'] == 'segment_length' else 'side' if prem['kind'] == 'base_is_square' else None
        if key:
            old_value = a[key]
            new_value = str(F(old_value.rstrip('a')) / 2) + 'a'
            old_quote = prem['quote']
            replace_quote(c, old_quote, old_quote.replace(old_value, new_value))
            next(x for x in c['payload']['premises'] if x['kind'] == prem['kind'] and x['quote'] == old_quote.replace(old_value, new_value))['args'][key] = new_value
    p = c['payload']
    for field in ('solid_vertices', 'named_points'):
        g[field] = {k: [str(F(x) / 2) for x in xyz] for k, xyz in g.get(field, {}).items()}
    for prem in list(p['premises']):
        if prem['kind'] == 'divide_segment':
            a = prem['args']; x, y = a['segment']
            t = F(index % 3 + 2, index % 3 + 7)
            if t == F(a['ratio']):
                t = (t + F(1,2)) / 2
            connector = ('sao cho', 'thỏa mãn', 'với', 'thỏa mãn')[style]
            forms = (f"Lấy {a['point']} thuộc cạnh {x}{y}", f"{a['point']} trên đoạn {x}{y}",
                     f"Trên đoạn {x}{y} chọn điểm {a['point']}", f"Chọn {a['point']} thuộc cạnh {x}{y}")
            old = prem['quote']; new = f"{forms[style]} {connector} {x}{a['point']} = {t} {x}{y}"
            replace_quote(c, old, new)
            next(x for x in c['payload']['premises'] if x['kind'] == 'divide_segment')['args']['ratio'] = str(t)
    p = c['payload']
    if group == 'projection':
        projection = next((x for x in p['premises'] if x['kind'] == 'orthogonal_projection'), None)
        solid = p['solids'][0]['notation']
        if projection is None:
            base, top = solid.split('.')
            if p['solids'][0]['solid_type'] == 'pyramid':
                point, plane = base, re.findall(r"[A-Z][0-9]*'?", top)
            else:
                plane = re.findall(r"[A-Z][0-9]*'?", base)
                point = re.findall(r"[A-Z][0-9]*'?", top)[0]
            projection = {'kind':'orthogonal_projection','args':{'point':point,'image':plane[0],'plane':plane},'solid_id':'s1'}
            q = f"Hình chiếu vuông góc của {point} lên mặt phẳng ({''.join(plane)}) là {plane[0]}"
            projection['quote'] = q
            p['premises'].append(projection)
            p['problem_text'] = q + '. ' + p['problem_text']
        a = projection['args']; point, foot, plane = a['point'], a['image'], ''.join(a['plane'])
        new = (f"Hình chiếu vuông góc của {point} lên mặt phẳng ({plane}) là {foot}",
               f"{foot} là chân đường cao hạ từ {point} xuống mặt phẳng ({plane})",
               f"Chân đường cao kẻ từ {point} đến mặt phẳng ({plane}) trùng với đỉnh {foot}",
               f"Kẻ đường cao từ {point} xuống mặt phẳng ({plane}) tại {foot}")[style]
        replace_quote(c, projection['quote'], new)
    elif style == 3:
        p = c['payload']; base = re.findall(r"[A-Z][0-9]*'?", p['solids'][0]['notation'].split('.')[-1 if p['solids'][0]['solid_type']=='pyramid' else 0])
        fresh = next(x for x in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if x not in set(g['solid_vertices']) | set(g['named_points']))
        x, y = base[:2]
        q = f'Chọn {fresh} thuộc cạnh {x}{y} với {x}{fresh} = 2/7 {x}{y}'
        old = next(x['quote'] for x in p['premises'] if x['kind']=='divide_segment')
        p['problem_text'] = p['problem_text'].replace(old + '.', old + ', và ' + q + '.')
        p['premises'].append({'kind':'divide_segment','args':{'point':fresh,'segment':[x,y],'ratio':'2/7'},'quote':q,'solid_id':'s1'})
    p = c['payload']
    if style == 1:
        q = next(x['quote'] for x in p['premises'] if x['kind']=='divide_segment')
        p['problem_text'] = q + '. ' + p['problem_text'].replace(q + '. ', '')
    c['problem_text'] = p['problem_text']
    refresh_points(c, g, independent)
    return c, g


def negative_cases(ratio_case, projection_case):
    out = []
    source_codes = ['SOURCE_OBJECT_MISMATCH','ROLE_NOT_IN_QUOTE','PLANE_NOT_IN_QUOTE','UNKNOWN_LABEL','SOURCE_PREMISE_UNREAD','INCONSISTENT_FACTS','QUESTION_LOCAL_GIVEN_CONFLICT','QUESTION_LOCAL_GIVEN_UNVERIFIED','CONFLICTING_FACTS','SCHEMA_INVALID','BRIDGE_UNKNOWN_SOLID','BRIDGE_UNSUPPORTED_MULTI_SOLID','FACT_INCOMPLETE','UNSUPPORTED_CAPABILITY','SOLID_MEMBERSHIP_MISMATCH']
    for i in range(1,25):
        c = deepcopy(ratio_case if i<=13 else projection_case)
        c['id'] = f'DEV-NEG-{i:02d}'; c['slice']='mandatory_negative_tamper';c['negative_class']=str(i)
        c['expected_disposition']='REFUSE'; c['acceptable_categories']=[];c['expected_codes']=list(source_codes)
        p=c['payload']; prem=next(x for x in p['premises'] if x['kind']==('divide_segment' if i<=13 else 'orthogonal_projection'))
        a=prem['args']; old=prem['quote']
        if i<=13:
            x,y=a['segment']; point=a['point']; t=F(a['ratio'])
            if i==1:a['ratio']=str(1/t); c['expected_codes']=['SCHEMA_INVALID','INVALID_RATIO']
            elif i==2:a['segment'][1]=next(v for v in p['premises'][0]['args'].get('vertices',[]) if v!=y and v!=x)
            elif i==3:a['segment']=list(reversed(a['segment']))
            elif i==4:replace_quote(c,old,old.replace(f'{x}{y}',f'{x}Z',1))
            elif i in (5,6):a['ratio']='-1/3' if i==5 else '4/3';c['expected_codes']=['SCHEMA_INVALID','INVALID_RATIO']
            elif i==7:replace_quote(c,old,old+f', và {x}{point} = 1/2 {x}{y}')
            elif i==8:prem['solid_id']='foreign';c['expected_codes']+=['BRIDGE_UNKNOWN_SOLID_ID','UNKNOWN_SOLID_ID']
            elif i==9:prem['quote']='Gọi Z thuộc cạnh XY với XZ = 1/3 XY';c['expected_codes']=['QUOTE_NOT_IN_SOURCE']
            elif i==10:a['ratio']='1/2'
            elif i==11:replace_quote(c,old,'Nếu '+old);c['expected_codes']=['CONDITIONAL_CLAUSE','SOURCE_OBJECT_MISMATCH']
            elif i==12:replace_quote(c,old,old.replace('với','với ghi chú riêng,'))
            elif i==13:
                replace_quote(c,old,f'{x}{point} = {t} {x}{y}')
                c['expected_codes']=['PREDICATE_NOT_IN_QUOTE','SOURCE_OBJECT_MISMATCH']
        else:
            point,foot,plane=a['point'],a['image'],''.join(a['plane']); other=next(v for v in a['plane'] if v!=foot)
            if i==14:a['image']=other
            elif i==15:a['point']=other
            elif i==16:a['plane']=[a['plane'][0],a['plane'][1],point]
            elif i==17:replace_quote(c,old,old.replace(f'mặt phẳng ({plane})',f'đường thẳng {a["plane"][0]}{a["plane"][1]}'))
            elif i==18:replace_quote(c,old,f'{foot} là chân đường cao của tam giác {point}{other}{foot}')
            elif i==19:replace_quote(c,old,old.replace('là chân','không phải chân'));c['expected_codes']=['NEGATED_CLAUSE','SOURCE_OBJECT_MISMATCH']
            elif i==20:
                bad=next(v for v in re.findall(r"[A-Z][0-9]*'?",p['solids'][0]['notation'].split('.')[1]) if v!=point)
                replace_quote(c,old,old.replace(foot+' là',bad+' là'));next(x for x in c['payload']['premises'] if x['kind']=='orthogonal_projection')['args']['image']=bad
                c['expected_codes']+=['ENGINE_INCONSISTENT_FACTS','ENGINE_CONSTRAINT_VIOLATION','PREMISE_NOT_SATISFIED','INCONSISTENT_GRAM','GRAM_INCONSISTENT','ENGINE_INCONSISTENT_GEOMETRY']
            elif i==21:replace_quote(c,old,old+f', và chân đường cao đó là {other}')
            elif i==22:a['point']=point.rstrip("'")
            elif i==23:prem['solid_id']='foreign';c['expected_codes']+=['BRIDGE_UNKNOWN_SOLID_ID','UNKNOWN_SOLID_ID']
            elif i==24:replace_quote(c,old,'Chứng minh rằng '+old);c['expected_codes']=['GOAL_CLAUSE_NOT_PREMISE','SOURCE_OBJECT_MISMATCH']
        c['problem_text']=c['payload']['problem_text']
        out.append(c)
    return out


def build():
    historical = load(HIST/'inputs/holdout-wave3.json')['cases']
    cases_by_id = {c['id']:c for c in historical}
    post = load(F1/'results/wave3-post-feedback-regression.json')['cases']
    ids = [c['id'] for c in post if c['expected']=='SERVE' and c['code']=='PREDICATE_NOT_IN_QUOTE']
    assert len(ids)==21
    independent=oracle_module(); geometry=load(HIST/'oracle/geometry.json')['cases']
    cases=[]; geometries={}; expected={}; groups={}
    for cid in ids:
        c=deepcopy(cases_by_id[cid]);c['slice']='historical_f2_verbatim'
        bad=[p['kind'] for p in c['payload']['premises'] if (p['kind']=='divide_segment' and not 'sao cho' in p['quote']) or (p['kind']=='orthogonal_projection' and 'chân đường cao' in p['quote'])]
        groups[cid]=sorted(set(bad))
        if cid=='W3-A06':c['known_independent_limit']='RADICAL_DOMAIN_CEILING'
        cases.append(c);geometries[cid]=deepcopy(geometry[cid]);expected[cid]=independent.compute_case_oracle(c,geometries[cid])
    # A smaller independently checked geometry isolates the language in the masked A06 case.
    c=deepcopy(cases_by_id['W3-A06']);c['id']='DEV-ISOLATED-A06';c['slice']='isolated_f2';g=deepcopy(geometry['W3-A06'])
    prem=next(x for x in c['payload']['premises'] if x['kind']=='segment_length' and x['args']['segment']==['S','E'])
    replace_quote(c,prem['quote'],prem['quote'].replace('15a','7a'))
    next(x for x in c['payload']['premises'] if x['kind']=='segment_length' and x['args']['segment']==['S','E'])['args']['value']='7a';g['solid_vertices']['S'][2]='7'
    refresh_points(c,g,independent);cases.append(c);geometries[c['id']]=g;expected[c['id']]=independent.compute_case_oracle(c,g)
    seeds=['W3-B04','W3-B13','W3-B22','W3-B31','W3-B40','W3-B49']
    for group in ('ratio','projection'):
        selected=seeds if group=='ratio' else ['W3-B04','W3-B13','W3-B31','W3-B04','W3-B13','W3-B31']
        for i,seed in enumerate(selected):
            for style in range(4):
                c,g=authored(cases_by_id[seed],geometry[seed],i*4+style+1,group,style,independent)
                cases.append(c);geometries[c['id']]=g;expected[c['id']]=independent.compute_case_oracle(c,g)
    # Two independently located midpoint feet on an oblique prism; new foot is not a solid vertex.
    for index in (25,26):
        c,g=authored(cases_by_id['W3-B31'],geometry['W3-B31'],index,'projection',1,independent)
        p=c['payload'];prem=next(x for x in p['premises'] if x['kind']=='orthogonal_projection');a=prem['args']
        oldfoot=a['image'];u,v=a['plane'][:2];foot=next(x for x in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if x not in set(g['solid_vertices'])|set(g['named_points']))
        target=[(F(x)+F(y))/2 for x,y in zip(g['solid_vertices'][u],g['solid_vertices'][v])];delta=[t-F(x) for t,x in zip(target,g['solid_vertices'][oldfoot])]
        for label in re.findall(r"[A-Z][0-9]*'?",p['solids'][0]['notation'].split('.')[1]):g['solid_vertices'][label]=[str(F(x)+d) for x,d in zip(g['solid_vertices'][label],delta)]
        replace_quote(c,prem['quote'],prem['quote'].replace(oldfoot+' là',foot+' là'))
        next(x for x in c['payload']['premises'] if x['kind']=='orthogonal_projection')['args']['image']=foot
        for length in list(c['payload']['premises']):
            if length['kind']=='segment_length' and set(length['args']['segment'])=={a['point'],oldfoot}:
                replace_quote(c,length['quote'],length['quote'].replace(''.join(length['args']['segment']),''.join(foot if x==oldfoot else x for x in length['args']['segment'])))
                next(x for x in c['payload']['premises'] if x['kind']=='segment_length' and x['args']['segment']==length['args']['segment'])['args']['segment']=[foot if x==oldfoot else x for x in length['args']['segment']]
        p=c['payload'];q=f'Gọi {foot} là trung điểm của {u}{v}';p['problem_text']=q+'. '+p['problem_text'];p['premises'].insert(0,{'kind':'midpoint','args':{'point':foot,'segment':[u,v]},'solid_id':'s1','quote':q});c['problem_text']=p['problem_text']
        if index==26:
            for relation in list(c['payload']['premises']):
                if relation['kind'] in ('divide_segment','orthogonal_projection'):
                    replace_quote(c,relation['quote'],relation['quote'].replace("'",'′'))
        refresh_points(c,g,independent);cases.append(c);geometries[c['id']]=g;expected[c['id']]=independent.compute_case_oracle(c,g)
    ratio=next(c for c in cases if c['id']=='DEV-RATIO-03')
    projection=next(c for c in cases if c['id']=='DEV-PROJECTION-10')
    cases+=negative_cases(ratio,projection)
    assert len(cases)==96 and len({c['id'] for c in cases})==96
    for c in cases:
        if c['expected_disposition']=='SERVE':
            expected[c['id']]['expected_source_relations']=[{'kind':p['kind'],'args':p['args'],'quote':p['quote']} for p in c['payload']['premises'] if p['kind'] in ('divide_segment','orthogonal_projection')]
    write_new(RUN/'inputs/development.json',{'schema':'W3_F2_DEVELOPMENT/1','classification':'DEVELOPMENT_EVALUATION','historical_f2_ids':ids,'historical_f2_groups':groups,'cases':cases})
    write_new(RUN/'inputs/oracle.json',{'schema':'W3_F2_INDEPENDENT_EXACT_ORACLE/1','method':'existing standalone Fraction oracle; no product geometry imports','geometry':geometries,'cases':expected})
    print('Preregistered',len(cases),'cases; historical F2 IDs:',len(ids))


def evaluate_case(case, expected=None, phase='green'):
    import evaluate_holdout_wave3 as E
    from app.ai.adapter4_route import run_typed_fact_next_v2_route, build_adapter4_response
    from app.simulation.geometry_functions.registry import chuan_hoa
    captured=[]
    def route(payload):
        r=run_typed_fact_next_v2_route(payload);captured.append(r);return r
    scored=E.score_case(case,expected,load(HIST/'refusal-taxonomy.json'),route_fn=route,adapter_fn=build_adapter4_response)
    r=captured[0] if captured else None
    if case['expected_disposition']=='REFUSE':
        scored['matches_expected']=not scored['served'] and scored['code'] in (case['expected_codes']+(['PREDICATE_NOT_IN_QUOTE'] if phase=='red' else []))
    elif case.get('known_independent_limit') and scored['code']=='ENGINE_EXECUTION_FAILED':
        scored['matches_expected']=bool(r and r.reason.startswith('RadicalDomainError:'))
        scored['known_independent_limit']=case['known_independent_limit']
    else:
        scored['matches_expected']=scored['outcome']=='SERVED_CORRECT'
    relations=(expected or {}).get('expected_source_relations',[])
    planned=(r.planner or {}).get('calls',[]) if r else []
    provenance=[]
    for rel in relations:
        want=rel['kind'];args=rel['args']
        matching=[call for call in planned if call['fn']==want and all(call['args'].get(k)==v for k,v in args.items())]
        # The bridge normalizes Unicode primes, as does the source gate.
        ok=any(chuan_hoa(rel['quote']) in [chuan_hoa(q) for q in call.get('source',{}).get('quotes',[])] for call in matching)
        if not ok:
            matching=[call for call in planned if call['fn']==want and chuan_hoa(json.dumps(call['args'],ensure_ascii=False,sort_keys=True))==chuan_hoa(json.dumps(args,ensure_ascii=False,sort_keys=True))]
            ok=any(chuan_hoa(rel['quote']) in [chuan_hoa(q) for q in call.get('source',{}).get('quotes',[])] for call in matching)
        provenance.append(ok)
    scored['source_relation_provenance']=provenance
    if scored['served'] and not all(provenance):scored['matches_expected']=False
    scored['slice']=case['slice']
    return scored


def evaluate(phase):
    def offline(*args,**kwargs):raise RuntimeError('OFFLINE_ONLY')
    socket.socket.connect=offline;socket.create_connection=offline
    doc=load(RUN/'inputs/development.json');oracle=load(RUN/'inputs/oracle.json')['cases']
    rows=[evaluate_case(c,oracle.get(c['id']),phase) for c in doc['cases']]
    groups={s:{'total':len(cs:=[x for x in rows if x['slice']==s]),'served_correct':sum(x['outcome']=='SERVED_CORRECT' for x in cs),'refused':sum(not x['served'] for x in cs),'matched_expected':sum(x['matches_expected'] for x in cs)} for s in sorted({x['slice'] for x in rows})}
    receipt={'classification':'DEVELOPMENT_EVALUATION','phase':phase,'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'input_sha256_lf':digest(RUN/'inputs/development.json'),'oracle_sha256_lf':digest(RUN/'inputs/oracle.json'),'live_provider_calls':0,'slices':groups,'wrong_served':sum(x['outcome']=='WRONG_SERVED' for x in rows),'cases':rows}
    write_new(RUN/f'results/{"red-before" if phase=="red" else "green-after"}.json',receipt)
    if phase=='green':write_new(RUN/'results/tamper-results.json',{'classification':'DEVELOPMENT_EVALUATION','cases':[x for x in rows if x['slice']=='mandatory_negative_tamper']})
    print(json.dumps({k:v for k,v in receipt.items() if k!='cases'},ensure_ascii=True))
    return rows


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--build',action='store_true');parser.add_argument('--phase',choices=('red','green'));args=parser.parse_args()
    if args.build:build()
    if args.phase:evaluate(args.phase)
