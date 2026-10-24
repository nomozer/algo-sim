import { readFileSync } from 'node:fs';
import { renderToString } from 'react-dom/server';
import * as THREE from 'three';
import { describe, it, expect } from 'vitest';
import { UnsupportedNotice } from '../../../components/SimulationWorkspace';
import { Scene3DExplorer } from './Scene3DExplorer';
import { khungNhinSuPham } from './scene3d-camera';
import { diemVanhCongBiChe } from './scene3d-edge-visibility';
import { diemHuuHan, phanTichToanHocCuaCanh, type Scene3D } from './scene3d-model';
import {
  buildObject3D,
  diemKhungNhin,
  diemVuaKhung,
  updateCanonicalEdgeVisibility,
} from './scene3d-view';

const rows = JSON.parse(readFileSync(new URL('../../../../../docs/evaluation/geometry/runs/simulation-visual-consistency-learning-ux/demos/audit_scenes.json', import.meta.url), 'utf8'));
const correctedRows = JSON.parse(readFileSync(new URL('../../../../../docs/evaluation/geometry/runs/geometric-visual-correctness-framing/demos/audit_scenes.json', import.meta.url), 'utf8'));

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

  it('keeps curved boundary points on the true radius-r surface and supports adaptive safe-area camera framing', () => {
    const sphere = correctedRows.find((r: any) => r.id === 'family11_sphere_plane_cut').scene.objects.find((o: any) => o.type === 'curved_solid');
    const center = sphere.anchor.map(Number);
    const r = Math.sqrt(Number(sphere.radius_sq));
    for (const p of diemHuuHan([sphere])) {
      const dist = Math.hypot(p[0] - center[0], p[1] - center[1], p[2] - center[2]);
      expect(dist).toBeLessThanOrEqual(r * (1 + 1e-6));
    }

    const pts = diemHuuHan(correctedRows[0].scene.objects);
    const defaultFit = khungNhinSuPham(pts, [], [], 50, 1440 / 900, [8, 5, 6], { tiLeDoc: 0.56, tiLeNgang: 0.62 });
    const panelFit = khungNhinSuPham(pts, [], [], 50, 1440 / 900, [8, 5, 6], {
      tiLeDoc: 0.52,
      tiLeNgang: 0.45,
      dichTamNgang: -0.22,
    });
    expect(defaultFit).not.toBeNull();
    expect(panelFit).not.toBeNull();
    expect(panelFit!.nhinVao[0]).not.toBeCloseTo(defaultFit!.nhinVao[0], 3);
  });

  it('classifies curved rim occlusion dynamically per camera orientation and avoids static half-circle assumptions', () => {
    const cylRow = correctedRows.find((r: any) => r.id === 'family09_cylinder_and_sections');
    const diemNen = diemHuuHan(cylRow.scene.objects);
    const root = new THREE.Group();
    for (const o of cylRow.scene.objects) {
      const g = buildObject3D(o, false, undefined, diemNen);
      if (g) root.add(g);
    }
    const camFront = new THREE.PerspectiveCamera(50, 1.5, 0.1, 200);
    camFront.up.set(0, 0, 1);
    camFront.position.set(8, 5, 6);
    camFront.lookAt(0, 0, 1.5);
    camFront.updateMatrixWorld();
    updateCanonicalEdgeVisibility(root, camFront, '1440x900@1');

    const parNode = root.children.find((c) => c.name === 'circle:td_sec_parallel')!;
    expect(parNode).toBeDefined();
    const sigFront = parNode.userData.curvedRimFlagSig as string;
    expect(sigFront).toContain('0');
    expect(sigFront).toContain('1');

    const camBack = new THREE.PerspectiveCamera(50, 1.5, 0.1, 200);
    camBack.up.set(0, 0, 1);
    camBack.position.set(-8, -5, 6);
    camBack.lookAt(0, 0, 1.5);
    camBack.updateMatrixWorld();
    updateCanonicalEdgeVisibility(root, camBack, '1440x900@1');
    const sigBack = parNode.userData.curvedRimFlagSig as string;
    expect(sigBack).toContain('0');
    expect(sigBack).toContain('1');
    expect(sigBack).not.toBe(sigFront);

    const vol = root.children.find((c) => c.name.startsWith('curved:'))!.userData.curvedSolidVolume;
    expect(diemVanhCongBiChe(new THREE.Vector3(2, 0, 1), new THREE.Vector3(8, 0, 4), [vol])).toBe(false);
    expect(diemVanhCongBiChe(new THREE.Vector3(-2, 0, 1), new THREE.Vector3(8, 0, 4), [vol])).toBe(true);
  });

  it('maintains step-invariant camera bounds for curved scenes when diemCanh is present', () => {
    const cylRow = correctedRows.find((r: any) => r.id === 'family09_cylinder_and_sections');
    const diemCanh = diemHuuHan(cylRow.scene.objects);
    const emptyRoot = new THREE.Group();
    const curvedOnlyRoot = new THREE.Group();
    const fullRoot = new THREE.Group();
    for (const o of cylRow.scene.objects) {
      const g = buildObject3D(o, false, undefined, diemCanh);
      if (g) {
        fullRoot.add(g);
        if (o.type === 'curved_solid' || o.type === 'circle3' || o.type === 'ellipse3') {
          curvedOnlyRoot.add(g.clone());
        }
      }
    }
    expect(diemKhungNhin(curvedOnlyRoot, true)).toEqual([]);
    const fitStep0 = khungNhinSuPham(diemVuaKhung(emptyRoot, diemCanh), [], [], 50, 1.5, [8, 5, 6]);
    const fitFull = khungNhinSuPham(diemVuaKhung(fullRoot, diemCanh), [], [], 50, 1.5, [8, 5, 6]);
    expect(fitFull).toEqual(fitStep0);
  });

  it('enforces honest normal-mode section depth prepasses, subtle passive plane opacity, and explicit X-ray mode', () => {
    const sphRow = correctedRows.find((r: any) => r.id === 'family11_sphere_plane_cut');
    const diemNen = diemHuuHan(sphRow.scene.objects);
    const sphObj = sphRow.scene.objects.find((o: any) => o.type === 'curved_solid');
    const secObj = sphRow.scene.objects.find((o: any) => o.type === 'circle3');
    const planeObj = sphRow.scene.objects.find((o: any) => o.type === 'plane3');

    const sphGroup = buildObject3D(sphObj, false, undefined, diemNen)!;
    const depthPrepasses = sphGroup.children.filter((c) => c.userData?.chieuSau || c.userData?.chieuSauMatTruoc);
    expect(depthPrepasses.map((c) => c.renderOrder).sort((a, b) => a - b)).toEqual([5, 7.5]);
    const sphereContours = sphGroup.children.filter((c) => (c as THREE.Line).isLine);
    expect(sphereContours.length).toBe(3);

    const secNormal = buildObject3D(secObj, false, undefined, diemNen, undefined, undefined, undefined, false)!;
    const fillNormal = secNormal.children.find((c) => c.name.startsWith('section_fill:')) as THREE.Mesh;
    expect((fillNormal.material as THREE.MeshStandardMaterial).depthTest).toBe(true);

    const secXray = buildObject3D(secObj, false, undefined, diemNen, undefined, undefined, undefined, true)!;
    const fillXray = secXray.children.find((c) => c.name.startsWith('section_fill:')) as THREE.Mesh;
    expect((fillXray.material as THREE.MeshStandardMaterial).depthTest).toBe(false);

    const planeGroup = buildObject3D(planeObj, false, undefined, diemNen)!;
    let planeOpacity = 1;
    planeGroup.traverse((c) => {
      if ((c as THREE.Mesh).isMesh) {
        planeOpacity = Math.min(planeOpacity, ((c as THREE.Mesh).material as THREE.MeshStandardMaterial).opacity);
      }
    });
    expect(planeOpacity).toBeLessThanOrEqual(0.07);
  });

  it('reconciles multi-solid visibility, secondary-solid differentiation, and student-facing demo identities', () => {
    const prismRow = correctedRows.find((r: any) => r.id === 'family05_prism');
    expect(prismRow.category).toBe('5. Hình lăng trụ đứng ABC.DEF');

    const multiRow = correctedRows.find((r: any) => r.id === 'family07_multi_solid_composition');
    expect(multiRow.category).toBe('7. Tổ hợp đa khối (Hai hình chóp S.ABC và D.ABC chung đáy ABC)');
    const notations = multiRow.scene.objects.filter((o: any) => o.type === 'point3').map((o: any) => o.notation);
    expect(notations).toContain('D1');
    expect(notations).not.toContain('D(pyr2)');

    const sphRow = correctedRows.find((r: any) => r.id === 'family11_sphere_plane_cut');
    const elRow = correctedRows.find((r: any) => r.id === 'family12_cylinder_ellipse_section');
    expect(JSON.stringify(sphRow)).not.toContain('qua đại lượng');
    expect(JSON.stringify(elRow)).not.toContain('qua đại lượng');

    const diemNen = diemHuuHan(multiRow.scene.objects);
    const root = new THREE.Group();
    const solids = multiRow.scene.objects.filter((o: any) => o.type === 'solid');
    const primaryGroup = buildObject3D(solids[0], false, undefined, diemNen)!;
    const secondaryGroup = buildObject3D(solids[1], false, undefined, diemNen)!;
    root.add(primaryGroup, secondaryGroup);

    const cam = new THREE.PerspectiveCamera(50, 1.5, 0.1, 200);
    cam.up.set(0, 0, 1);
    cam.position.set(8, 5, 6);
    cam.lookAt(0, 0, 2);
    cam.updateMatrixWorld();
    const audit = updateCanonicalEdgeVisibility(root, cam, '1440x900@1');
    expect(audit.duplicate_visual_owner_ids).toEqual([]);
    expect(audit.visible_edge_ids.length).toBeGreaterThan(0);
    expect(audit.hidden_edge_ids.length).toBeGreaterThan(0);
  });
});
