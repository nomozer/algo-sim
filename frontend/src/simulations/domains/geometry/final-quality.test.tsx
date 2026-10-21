import { readFileSync } from 'node:fs';
import { renderToString } from 'react-dom/server';
import { describe, it, expect } from 'vitest';
import { UnsupportedNotice } from '../../../components/SimulationWorkspace';
import { Scene3DExplorer } from './Scene3DExplorer';
import { diemHuuHan, phanTichToanHocCuaCanh, type Scene3D } from './scene3d-model';

const rows = JSON.parse(readFileSync(new URL('../../../../../docs/evaluation/geometry/runs/simulation-visual-consistency-learning-ux/demos/audit_scenes.json', import.meta.url), 'utf8'));
describe('final visual quality', () => {
  it('encloses curved surfaces in diagonal camera directions before their geometry is constructed', () => {
    const sphere=rows.find((r:any)=>r.id==='family11_sphere_plane_cut').scene.objects.find((o:any)=>o.type==='curved_solid');
    const center=sphere.anchor.map(Number), r=Math.sqrt(Number(sphere.radius_sq));
    const support=Math.max(...diemHuuHan([sphere]).map(p=>p.reduce((sum,v,i)=>sum+v-center[i],0)));
    expect(support).toBeGreaterThanOrEqual(r*Math.sqrt(3));
    const cylinder=rows.find((r:any)=>r.id==='family09_cylinder_and_sections').scene.objects.find((o:any)=>o.type==='curved_solid');
    const c=cylinder.anchor.map(Number), radius=Math.sqrt(Number(cylinder.radius_sq));
    expect(Math.max(...diemHuuHan([cylinder]).map(p=>p[0]-c[0]+p[1]-c[1]))).toBeGreaterThanOrEqual(radius*Math.sqrt(2));
  });
  it('explains a nonintersecting sphere without an unsupported-family label or raw codes in the main text', () => {
    const html = renderToString(<UnsupportedNotice unsupported={{ reason:'CURVED_PLANE_DOES_NOT_CUT: CURVED_PLANE_DOES_NOT_CUT: mặt phẳng cách tâm mặt cầu một khoảng lớn hơn bán kính.', error_code:'CURVED_PLANE_DOES_NOT_CUT', failure_category:'postcondition_violated', refusal_cause:'SOURCE' }}/>);
    const main = html.replace(/<details[\s\S]*?<\/details>/g,'');
    expect(main).toContain('mặt phẳng cách tâm mặt cầu một khoảng lớn hơn bán kính');
    expect(main).not.toContain('CURVED_');
    expect(main).not.toContain('NGOÀI DANH MỤC');
    expect(html).toContain('<details');
    expect(html).toContain('CURVED_PLANE_DOES_NOT_CUT');
  });
  it.each(['Mặt phẳng nằm ngoài chiều cao hình trụ.', 'Mặt phẳng chỉ đi qua đỉnh hình nón.'])('keeps the authoritative nonintersection explanation for %s', reason => {
    const html=renderToString(<UnsupportedNotice unsupported={{reason, error_code:'CURVED_PLANE_DOES_NOT_CUT'}}/>);
    const main=html.replace(/<details[\s\S]*?<\/details>/g,'');
    expect(main).toContain(reason);
    expect(main).not.toContain('mặt cầu');
    expect(main).not.toContain('CURVED_');
  });
  it.each([
    ['CURVED_PRIMITIVE_BLOCKED_BY_KERNEL','NGOÀI PHẠM VI DỰNG HÌNH'],
    ['INCONSISTENT_FACTS','DỮ KIỆN MÂU THUẪN'],
    ['MISSING_CURVED_DIMENSION','CHƯA ĐỦ DỮ KIỆN'],
    ['AMBIGUOUS_REFERENCE','CHƯA XÁC ĐỊNH DUY NHẤT'],
    ['postcondition_violated','CHƯA KIỂM CHỨNG ĐƯỢC MÔ PHỎNG'],
  ])('presents the semantic refusal class for %s', (error_code,title) => {
    expect(renderToString(<UnsupportedNotice unsupported={{reason:'Không dựng được.', error_code}}/>)).toContain(title);
  });
  it('resolves analysis solid references and hides unknown machine names', () => {
    const row=rows.find((r:any)=>r.id==='family10_cone_frustum_cut');
    const analysis=phanTichToanHocCuaCanh(row.scene,null,row.route_d);
    const shown=JSON.stringify(analysis.requestedResults.map(({label,notation,basisLabels})=>({label,notation,basisLabels})));
    expect(shown).not.toMatch(/cone_main|cone_upper/);
    expect(shown).toContain('Hình nón');
    const unknown=phanTichToanHocCuaCanh({objects:[],events:[],free_objects:[]} as Scene3D,null,{math_goals:[{goal_id:'secret_goal_4',kind:'volume_ratio',numerator_solid:'missing_solid_1',denominator_solid:'missing_solid_2',value_display:'1/8'}]});
    expect(JSON.stringify(unknown.requestedResults.map(({label,notation})=>({label,notation})))).not.toMatch(/missing_solid|secret_goal/);
  });
  it('preserves genuine symbolic units and makes given quantities consistent with them', () => {
    const row=rows.find((r:any)=>r.id==='family12_cylinder_ellipse_section');
    const analysis=phanTichToanHocCuaCanh(row.scene,null,row.route_d);
    expect(analysis.requestedResults.map(x=>x.valueDisplay)).toEqual(['4π√2a^2','24πa^3']);
    expect(analysis.lengthUnit).toBe('a');
    expect(analysis.givenDimensions.map(x=>x.valueDisplay)).toEqual(['2','6']);
    const unitless=rows.find((r:any)=>r.id==='family09_cylinder_and_sections');
    expect(phanTichToanHocCuaCanh(unitless.scene,null,unitless.route_d).givenDimensions.map(x=>x.valueDisplay)).toEqual(['2','3']);
  });
  it('provides entry guidance and a complete-model action without opening analysis', () => {
    const html=renderToString(<Scene3DExplorer scene={rows[0].scene}/>);
    expect(html).toContain('Bấm Phát hoặc Bước sau');
    expect(html).toContain('Xem mô hình đầy đủ');
    expect(html).not.toContain('data-math-analysis-panel');
  });
});
