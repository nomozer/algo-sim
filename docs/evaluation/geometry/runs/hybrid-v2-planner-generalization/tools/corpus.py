"""Finite authored development corpus; registration precedes product modification.

All route inputs are source-bound TypedFacts. Explicit Euclidean coordinates belong only to the independent oracle.
Run this script once to register inputs/development.json and inputs/oracle.json; existing evidence is never overwritten.
"""
from copy import deepcopy
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path


def _load_oracle():
    path = Path(__file__).with_name('oracle.py')
    spec = importlib.util.spec_from_file_location('prism_section_oracle', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fact(fid, kind, quote, role='premise', **kw):
    return dict(id=fid, kind=kind, role=role, quotes=[quote], **kw)


def positive(cid, family='triangle', line=('A','B'), dims=(6,8,12), symbolic=False, labels='ABC', reverse=False):
    x,y,h = dims
    base = list(labels if family in ('triangle','oblique') else 'ABCD')
    top = [v+"'" for v in base]
    name = ''.join(base)+'.'+''.join(top)
    a,b,c = base[:3]
    oblique = family == 'oblique'
    word = 'hình lập phương' if family == 'cube' else 'hình hộp chữ nhật' if family == 'cuboid' else 'lăng trụ' if oblique else 'lăng trụ đứng'
    declaration = f'Cho {word} {name}.'
    facts = [_fact('solid','solid', declaration, solid=name,
                   solid_type=family if family in ('cube','cuboid') else 'prism', right=not oblique)]
    def value(v): return str(v)+('a' if symbolic else '')
    def length(fid, u,v,n):
        facts.append(_fact(fid,'length',f'{u}{v} = {value(n)}.', points=[u,v],measure='segment',value=value(n)))
    if len(base)==3:
        facts.append(_fact('shape','right_angle',f'Đáy {a}{b}{c} là tam giác vuông tại {a}.',at=a,points=[b,c]))
        length('ab',a,b,x); length('ac',a,c,y)
        coords = {a:(0,0,0),b:(x,0,0),c:(0,y,0)}
    else:
        facts.append(_fact('shape','polygon_shape',f'Đáy {"".join(base)} là hình chữ nhật.',points=base,shape='rectangle'))
        length('ab',a,b,x); length('ad',a,base[3],y)
        coords = {a:(0,0,0),b:(x,0,0),c:(x,y,0),base[3]:(0,y,0)}
    lateral=(0,0,h)
    if oblique:
        # x=6,y=8,h=12 => AA'=13, independently 3²+4²+12²=13².
        assert (x,y,h)==(6,8,12)
        facts += [_fact('foot','point_def',f'Gọi H là trung điểm của {b}{c}.',point='H',point_kind='midpoint',points=[b,c]),
                  _fact('projection','projection',f'Hình chiếu vuông góc của {a}\' lên ({"".join(base)}) là H.',
                        point=a+"'",points=base,at='H')]
        coords['H']=(F(x,2),F(y,2),0)
        lateral=(F(x,2),F(y,2),h)
        length('height',a,a+"'",13)
    else:
        length('height',a,a+"'",h)
    for v in base: coords[v+"'"]=tuple(q+r for q,r in zip(coords[v],lateral))
    segment=[b,c+"'"] if len(base)==3 else [a,c+"'"]
    coords['M']=tuple((u+v)/2 for u,v in zip(coords[segment[0]],coords[segment[1]]))
    facts.append(_fact('mid','point_def',f'Gọi M là trung điểm của {"".join(segment)}.',point='M',point_kind='midpoint',points=segment))
    mapping=dict(zip('ABC',base)) | {v+"'": base[i]+"'" for i,v in enumerate('ABC')}
    d=[mapping.get(v,v) for v in line]
    definition=f'Dựng mặt phẳng (P) đi qua M và vuông góc với {"".join(d)}.'
    secask=f'Dựng thiết diện của {word} {name} với (P).'
    areaask=f'Tính diện tích thiết diện của {word} {name} với (P).'
    common=dict(solid=name,point='M',points_b=d,plane_relation='perpendicular')
    facts += [_fact('sec','section',definition+' '+secask,role='question',**common),
              _fact('q','question',definition+' '+areaask,role='question',quantity='area',**common)]
    text=' '.join(dict.fromkeys(q for f in facts for q in f['quotes']))
    if reverse: facts.reverse()
    geometry=dict(points={k:list(map(str,v)) for k,v in coords.items()},base=base,top=top,point='M',line=d)
    return dict(id=cid,family=family,text=text,payload={'facts':facts},geometry=geometry,
                expected_status='SERVED',expected_codes=[],unit='a^2' if symbolic else '1')


def cases():
    rows=[positive('right-base'),positive('right-top',line=("A'","B'")),
          positive('right-lateral',line=('A',"A'")),positive('right-diagonal',line=('B',"C'")),
          positive('cuboid-base',family='cuboid'),positive('cube-diagonal',family='cube',dims=(4,4,4),line=('A',"C'")),
          positive('oblique-base',family='oblique'),positive('oblique-diagonal',family='oblique',line=('A',"C'")),
          positive('renamed-changed-reversed',dims=(3,4,5),labels='DEF',line=("C'",'B'),reverse=True),
          positive('symbolic-top',line=("B'","A'"),symbolic=True)]
    for row in rows:
        result=_load_oracle().section(row['geometry'])
        assert result['interior_cut'] and F(result['area_squared'])>0, row['id']
        row['expected_area_squared']=result['area_squared']
    def negative(cid,codes,change):
        row=deepcopy(rows[0]); row.update(id=cid,expected_status='REFUSED',expected_codes=codes)
        change(row); row['geometry']=None; row['expected_area_squared']=None
        rows.append(row)
    def remove_height(r):
        f=next(f for f in r['payload']['facts'] if f['id']=='height')
        r['text']=r['text'].replace(f['quotes'][0],''); r['payload']['facts'].remove(f)
    negative('missing-dimension',['MISSING_DIMENSION'],remove_height)
    def contradiction(r):
        r['text']+=' AA\' = 13.'
        r['payload']['facts'].append(_fact('conflict','length',"AA' = 13.",points=['A',"A'"],measure='segment',value='13'))
    negative('conflicting-length',['INCONSISTENT_FACTS'],contradiction)
    def constructed(r):
        old='vuông góc với AB'; new='vuông góc với AM'
        r['text']=r['text'].replace(old,new)
        for f in r['payload']['facts']:
            if f['id'] in ('sec','q'):
                f['points_b']=['A','M']; f['quotes']=[q.replace(old,new) for q in f['quotes']]
    negative('constructed-line-endpoint',['UNSUPPORTED_CAPABILITY'],constructed)
    def mismatch(r):
        r['text']=r['text'].replace('vuông góc với AB','vuông góc với AC')
        for f in r['payload']['facts']:
            f['quotes']=[q.replace('vuông góc với AB','vuông góc với AC') for q in f['quotes']]
    negative('wrong-source-line',['SOURCE_OBJECT_MISMATCH'],mismatch)
    def unmentioned(r):
        for f in r['payload']['facts']:
            if f['id'] in ('sec','q'): f['points_b']=['A','Z']
    negative('unmentioned-line-endpoint',['UNSUPPORTED_CAPABILITY'],unmentioned)
    def plane_perp(r):
        r['text']=r['text'].replace('vuông góc với AB','vuông góc với (ABC)')
        for f in r['payload']['facts']:
            if f['id'] in ('sec','q'):
                f['points_b']=list('ABC'); f['quotes']=[q.replace('vuông góc với AB','vuông góc với (ABC)') for q in f['quotes']]
    negative('plane-perpendicular-plane',['PLANE_NOT_UNIQUE'],plane_perp)
    def point_and_line(r,p,line):
        r['text']=r['text'].replace('đi qua M và vuông góc với AB',f'đi qua {p} và vuông góc với {"".join(line)}')
        for f in r['payload']['facts']:
            if f['id'] in ('sec','q'):
                f['point']=p; f['points_b']=line
                f['quotes']=[q.replace('đi qua M và vuông góc với AB',f'đi qua {p} và vuông góc với {"".join(line)}') for q in f['quotes']]
    negative('boundary-face',['SECTION_PLANE_IS_FACE'],lambda r:point_and_line(r,'A',['A','B']))
    negative('vertex-touch',['PLANE_TOUCHES_VERTEX','PLANE_DOES_NOT_CUT'],lambda r:point_and_line(r,"C'",['A',"C'"]))
    return rows


def canonical(row):
    """Translate this fixture's declared source premises into existing canonical V2 forms, without product inference."""
    fs=row['payload']['facts']; sol=next(f for f in fs if f['id']=='solid'); g=row['geometry']
    premises=[]
    for f in fs:
        q=f['quotes'][0]; k=f['kind']
        if k=='right_angle': premises.append(dict(kind='right_angle',args=dict(vertex=f['at'],rays=f['points']),quote=q))
        elif k=='length': premises.append(dict(kind='segment_length',args=dict(segment=f['points'],value=f['value']),quote=q))
        elif k=='point_def': premises.append(dict(kind='midpoint',args=dict(point=f['point'],segment=f['points']),quote=q))
        elif k=='projection': premises.append(dict(kind='orthogonal_projection',args=dict(point=f['point'],image=f['at'],plane=f['points']),quote=q))
        elif k=='polygon_shape': premises.append(dict(kind='rectangle',args=dict(vertices=f['points']),quote=q))
    if sol['right']: premises.append(dict(kind='right_prism',args=dict(base=g['base'],top=g['top']),quote=sol['quotes'][0]))
    sec=next(f for f in fs if f['id']=='sec'); ask=next(f for f in fs if f['id']=='q')
    return dict(schema_version='typed-fact-next/2',problem_text=row['text'],length_unit='a' if row['unit']=='a^2' else '1',
        solids=[dict(solid_id='pr',solid_type='prism',notation=sol['solid'],quote=sol['quotes'][0])],premises=premises,
        derived_sections=[dict(section_id='sec',plane_name='P',target_solid_id='pr',plane_kind='through_point_perpendicular_line',
                               through_point='M',perpendicular_line=g['line'],quote=sec['quotes'][0])],
        simulation_goals=[dict(goal_id='draw',kind='construct_plane_section',target_section_id='sec',quote=sec['quotes'][0])],
        math_goals=[dict(goal_id='q',kind='measurement',goal_type='area',target={'section_id':'sec'},quote=ask['quotes'][0])])


if __name__=='__main__':
    run=Path(__file__).resolve().parents[1]
    paths=[run/'inputs/development.json',run/'inputs/oracle.json']
    if any(p.exists() for p in paths): raise SystemExit('refusing overwrite of registered inputs')
    data=cases()
    oracle={r['id']:_load_oracle().section(r['geometry']) for r in data if r['geometry']}
    paths[0].parent.mkdir(parents=True,exist_ok=True)
    paths[0].write_text(json.dumps(dict(classification='AUTHORED_DEVELOPMENT_NOT_HOLDOUT',live_calls=0,cases=data),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    paths[1].write_text(json.dumps(oracle,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'registered {len(data)} DEV cases, {len(oracle)} exact oracle sections')
