/**
 * sample-catalog-meta.ts — Bảng metadata siêu nhẹ (không chứa JSON scene3d/frames,
 * không kéo `three` hay `scene3d-semantic-policy.ts`) cho toàn bộ 22 bài mẫu hình học.
 *
 * Dùng cho: định tuyến `/simulation/<slug>`, Thư viện (`/library`), Thanh bên (`LeftSidebar`),
 * nhận diện tab/họ hình, và khôi phục nhanh từ bộ nhớ đệm sau khi tải động payload.
 */
import type { GeometryFamilyId } from "../components/geometry2d/family-icons";
import type {
  GeometryTemplateId,
  VerifiedTemplateLabels,
} from "../components/geometry2d/templates";
import {
  geometryStepCount,
  hopLeScene3D,
} from "../simulations/domains/geometry/scene3d-model";
import { getSimulation } from "../simulations/registry";
import type { Domain, SimulationEnvelope } from "../simulations/types";
import { historyIdOf } from "../state/history";

export type SampleSolidFamily =
  | "pyramid"
  | "cube"
  | "prism"
  | "sphere"
  | "cylinder"
  | "cone"
  | "neutral";

export interface SampleIllustrationMeta {
  readonly mode: "verified" | "generic" | "family-icon" | "fallback-neutral";
  readonly family: GeometryFamilyId;
  readonly templateId: GeometryTemplateId | null;
  readonly fallback: boolean;
  readonly labels: VerifiedTemplateLabels | null;
}

export interface SampleCatalogMeta {
  readonly id: string;
  readonly slug: string;
  readonly title: string;
  readonly group: string;
  readonly simId: string;
  readonly domain: Domain;
  readonly visibility: "public" | "internal_fixture";
  readonly problemText: string;
  readonly description: string | null;
  readonly stepCount: number;
  readonly configHash: string;
  readonly historyId: string;
  readonly solidFamily: SampleSolidFamily;
  readonly illustration: SampleIllustrationMeta;
}

export interface CachedSampleRecord {
  readonly id: string;
  readonly slug: string;
  readonly title: string;
  readonly group: string;
  readonly simId: string;
  readonly domain: Domain;
  readonly visibility: "public" | "internal_fixture";
  readonly problemText: string;
  readonly envelope: SimulationEnvelope;
}

export const CANONICAL_SAMPLE_SLUGS: Readonly<Record<string, string>> = Object.freeze({
  "chop-thiet-dien-ba-diem": "pyramid-three-point-section",
  "lap-phuong-thiet-dien-bat-ky": "cube-hexagonal-plane-section",
  "khoang-cach-diem-mat-phang-nghieng": "point-to-inclined-plane-distance",
  "goc-nhi-dien-hai-mat-phang": "dihedral-angle-between-planes",
  "khoang-cach-hai-duong-cheo-nhau": "skew-lines-common-perpendicular",
  "lang-tru-tam-giac-thiet-dien": "triangular-prism-plane-section",
  "mat-cau-cat-mat-phang": "sphere-secant-plane-intersection",
  "oxyz-giao-diem-duong-mat": "oxyz-line-plane-intersection",
  "mat-phang-tiep-xuc-mat-cau": "sphere-tangent-plane-contact",
  "hinh-non-cat-song-song-day": "cone-parallel-base-section",
  "chop-mat-cau-ngoai-tiep": "pyramid-circumscribed-sphere",
  "thiet-dien-chop": "pyramid-cross-section",
  "mat-cheo-sac": "pyramid-diagonal-section",
  "vuong-goc-chop": "pyramid-line-plane-angle",
  "mp-vuong-goc-duong": "pyramid-perpendicular-plane-distance",
  "the-tich-chop": "pyramid-volume-and-altitude",
  "cau-cat-mat-phang": "sphere-plane-intersection",
  "cau-the-tich": "sphere-radius-and-volume",
  "tru-thiet-dien-tron": "cylinder-perpendicular-section",
  "tru-truc-xien": "tilted-right-cylinder-metrics",
  "non-thiet-dien-truc": "cone-axial-section",
  "non-duong-sinh": "cone-slant-height-and-surface",
});

export const PRODUCT_DOMAINS: readonly Domain[] = ["geometry"];

export const LIBRARY_CATEGORY_ORDER = [
  "all",
  "Hình chóp",
  "Hình lăng trụ",
  "Mặt cầu",
  "Hình trụ",
  "Hình nón",
  "Tọa độ Oxyz",
] as const;

export type LibraryCategory = (typeof LIBRARY_CATEGORY_ORDER)[number];

export const STARTER_SAMPLE_IDS = [
  "chop-thiet-dien-ba-diem",
  "mat-cau-cat-mat-phang",
  "lap-phuong-thiet-dien-bat-ky",
  "hinh-non-cat-song-song-day",
];

export const ALL_SAMPLE_META: readonly SampleCatalogMeta[] = Object.freeze([
  {
    "id": "chop-thiet-dien-ba-diem",
    "slug": "pyramid-three-point-section",
    "title": "Thiết diện hình chóp S.ABCD cắt bởi mặt phẳng (MNP)",
    "group": "Dựng hình · thiết diện",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "public",
    "problemText": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông tâm O cạnh bằng 4, cạnh bên SA vuông góc với mặt phẳng đáy (ABCD) và SA = 6. Gọi M là trung điểm của cạnh SA, N là trung điểm của cạnh BC và P là trung điểm của cạnh CD. Mặt phẳng (MNP) cắt cạnh SB tại E và cắt cạnh SD tại F. Xác định các giao tuyến của mặt phẳng (MNP) với các mặt của hình chóp, dựng thiết diện ngũ giác MENPF và tính diện tích thiết diện.",
    "description": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông tâm O cạnh bằng 4, cạnh bên SA vuông góc với mặt phẳng đáy (ABCD) và SA = 6. Gọi M là trung điểm của cạnh SA, N là trung điểm của cạnh BC và P là trung điểm của cạnh CD. Mặt phẳng (MNP) cắt cạnh SB tại E và cắt cạnh SD tại F. Xác định các giao tuyến của mặt phẳng (MNP) với các mặt của hình chóp, dựng thiết diện ngũ giác MENPF và tính diện tích thiết diện.",
    "stepCount": 12,
    "configHash": "ddb5190b1326d69e",
    "historyId": "hhvd1wb",
    "solidFamily": "pyramid",
    "illustration": {
      "mode": "verified",
      "family": "pyramid",
      "templateId": "pyramid.section",
      "fallback": false,
      "labels": {
        "apex": "S",
        "base": [
          "A",
          "B",
          "C",
          "D"
        ],
        "section": [
          "M",
          "E",
          "F",
          "N"
        ],
        "plane": "(MNP)"
      }
    }
  },
  {
    "id": "lap-phuong-thiet-dien-bat-ky",
    "slug": "cube-hexagonal-plane-section",
    "title": "Thiết diện lục giác đều của hình lập phương ABCD.A'B'C'D'",
    "group": "Dựng hình · thiết diện",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "public",
    "problemText": "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 4. Gọi M là trung điểm cạnh AD, N là trung điểm cạnh CD và P là trung điểm cạnh B'C'. Mặt phẳng (MNP) cắt các cạnh CC', A'B', AA' lần lượt tại các trung điểm E, F, Q tạo thành thiết diện lục giác đều MNEPFQ. Xác định các giao điểm trên 6 cạnh của hình lập phương, dựng thiết diện MNEPFQ và tính diện tích thiết diện.",
    "description": "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 4. Gọi M là trung điểm cạnh AD, N là trung điểm cạnh CD và P là trung điểm cạnh B'C'. Mặt phẳng (MNP) cắt các cạnh CC', A'B', AA' lần lượt tại các trung điểm E, F, Q tạo thành thiết diện lục giác đều MNEPFQ. Xác định các giao điểm trên 6 cạnh của hình lập phương, dựng thiết diện MNEPFQ và tính diện tích thiết diện.",
    "stepCount": 12,
    "configHash": "8931d62287704613",
    "historyId": "hf6xwpn",
    "solidFamily": "cube",
    "illustration": {
      "mode": "verified",
      "family": "pyramid",
      "templateId": "cube.plane-section",
      "fallback": false,
      "labels": {
        "base": [
          "A",
          "B",
          "C",
          "D"
        ],
        "section": [
          "M",
          "N",
          "E",
          "P",
          "F",
          "Q"
        ],
        "plane": "(MNP)"
      }
    }
  },
  {
    "id": "khoang-cach-diem-mat-phang-nghieng",
    "slug": "point-to-inclined-plane-distance",
    "title": "Khoảng cách từ điểm A đến mặt phẳng nghiêng (SBC)",
    "group": "Khoảng cách · thể tích · góc",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "public",
    "problemText": "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = 3, BC = 4, cạnh bên SA vuông góc với mặt phẳng đáy (ABC) và SA = 6. Từ chân đường cao A, hạ AH vuông góc với mặt phẳng nghiêng (SBC) tại H (H thuộc cạnh SB vì BC ⊥ (SAB)). Xác định hình chiếu vuông góc H, kiểm chứng AH ⊥ (SBC) và tính khoảng cách d(A, (SBC)) = AH.",
    "description": "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = 3, BC = 4, cạnh bên SA vuông góc với mặt phẳng đáy (ABC) và SA = 6. Từ chân đường cao A, hạ AH vuông góc với mặt phẳng nghiêng (SBC) tại H (H thuộc cạnh SB vì BC ⊥ (SAB)). Xác định hình chiếu vuông góc H, kiểm chứng AH ⊥ (SBC) và tính khoảng cách d(A, (SBC)) = AH.",
    "stepCount": 7,
    "configHash": "4eda4293caed8425",
    "historyId": "ht0aio0",
    "solidFamily": "pyramid",
    "illustration": {
      "mode": "verified",
      "family": "pyramid",
      "templateId": "pyramid.point-to-plane-distance",
      "fallback": false,
      "labels": {
        "apex": "S",
        "base": [
          "A",
          "B",
          "C"
        ],
        "foot": "H",
        "plane": "(SBC)"
      }
    }
  },
  {
    "id": "goc-nhi-dien-hai-mat-phang",
    "slug": "dihedral-angle-between-planes",
    "title": "Góc nhị diện [S, BC, A] giữa hai mặt phẳng (SBC) và (ABC)",
    "group": "Khoảng cách · thể tích · góc",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "public",
    "problemText": "Cho hình chóp S.ABC có đáy ABC là tam giác cân tại A với AB = AC = 5, BC = 6, cạnh bên SA vuông góc với mặt phẳng đáy (ABC) và SA = 4. Xác định giao tuyến BC của hai mặt phẳng (SBC) và (ABC), dựng trung điểm H của BC sao cho AH ⊥ BC và SH ⊥ BC, dựng mặt phẳng (SAH) vuông góc với giao tuyến BC tại H và tính cosin của góc phẳng nhị diện SHA của góc nhị diện [S, BC, A].",
    "description": "Cho hình chóp S.ABC có đáy ABC là tam giác cân tại A với AB = AC = 5, BC = 6, cạnh bên SA vuông góc với mặt phẳng đáy (ABC) và SA = 4. Xác định giao tuyến BC của hai mặt phẳng (SBC) và (ABC), dựng trung điểm H của BC sao cho AH ⊥ BC và SH ⊥ BC, dựng mặt phẳng (SAH) vuông góc với giao tuyến BC tại H và tính cosin của góc phẳng nhị diện SHA của góc nhị diện [S, BC, A].",
    "stepCount": 9,
    "configHash": "50a1ad1a4ce52c98",
    "historyId": "h1cb8s8d",
    "solidFamily": "pyramid",
    "illustration": {
      "mode": "verified",
      "family": "pyramid",
      "templateId": "pyramid.dihedral-angle",
      "fallback": false,
      "labels": {
        "apex": "S",
        "base": [
          "A",
          "B",
          "C"
        ],
        "foot": "H",
        "plane": "(SBC)"
      }
    }
  },
  {
    "id": "khoang-cach-hai-duong-cheo-nhau",
    "slug": "skew-lines-common-perpendicular",
    "title": "Đoạn vuông góc chung và khoảng cách giữa hai đường chéo nhau SC và BD",
    "group": "Khoảng cách · thể tích · góc",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "public",
    "problemText": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh bằng 4, cạnh bên SA vuông góc với mặt phẳng đáy (ABCD) và SA = 4. Hai đường thẳng SC và BD chéo nhau. Gọi Q là giao điểm hai đường chéo AC và BD (trung điểm của BD), từ Q kẻ QP vuông góc với SC tại P. Chứng minh PQ là đoạn vuông góc chung của hai đường thẳng chéo nhau SC và BD, và tính khoảng cách d(SC, BD) = PQ.",
    "description": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh bằng 4, cạnh bên SA vuông góc với mặt phẳng đáy (ABCD) và SA = 4. Hai đường thẳng SC và BD chéo nhau. Gọi Q là giao điểm hai đường chéo AC và BD (trung điểm của BD), từ Q kẻ QP vuông góc với SC tại P. Chứng minh PQ là đoạn vuông góc chung của hai đường thẳng chéo nhau SC và BD, và tính khoảng cách d(SC, BD) = PQ.",
    "stepCount": 10,
    "configHash": "e86996ac18f4e95e",
    "historyId": "hbr5e1e",
    "solidFamily": "pyramid",
    "illustration": {
      "mode": "verified",
      "family": "pyramid",
      "templateId": "pyramid.skew-lines-distance",
      "fallback": false,
      "labels": {
        "apex": "S",
        "base": [
          "A",
          "B",
          "C",
          "D"
        ],
        "foot": "P",
        "center": "Q",
        "plane": "(SAC)"
      }
    }
  },
  {
    "id": "lang-tru-tam-giac-thiet-dien",
    "slug": "triangular-prism-plane-section",
    "title": "Thiết diện ngũ giác của lăng trụ đứng ABC.A'B'C' cắt bởi mặt phẳng (NPQ)",
    "group": "Dựng hình · thiết diện",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "public",
    "problemText": "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại A với AB = AC = 4, cạnh bên AA' = 4. Gọi N là trung điểm cạnh BC, P là trung điểm cạnh CC' và Q là trung điểm cạnh A'C'. Mặt phẳng (NPQ) cắt cạnh AB tại M (AM = 3/4 AB) và cắt cạnh A'B' tại E (A'E = 1/4 A'B'). Xác định các giao tuyến trên cả 5 mặt của lăng trụ, dựng thiết diện ngũ giác MNPQE và tính diện tích thiết diện.",
    "description": "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại A với AB = AC = 4, cạnh bên AA' = 4. Gọi N là trung điểm cạnh BC, P là trung điểm cạnh CC' và Q là trung điểm cạnh A'C'. Mặt phẳng (NPQ) cắt cạnh AB tại M (AM = 3/4 AB) và cắt cạnh A'B' tại E (A'E = 1/4 A'B'). Xác định các giao tuyến trên cả 5 mặt của lăng trụ, dựng thiết diện ngũ giác MNPQE và tính diện tích thiết diện.",
    "stepCount": 11,
    "configHash": "466ec5b6ca9c3b4c",
    "historyId": "h12w4uzc",
    "solidFamily": "prism",
    "illustration": {
      "mode": "verified",
      "family": "pyramid",
      "templateId": "prism.plane-section",
      "fallback": false,
      "labels": {
        "base": [
          "A",
          "B",
          "C"
        ],
        "section": [
          "M",
          "N",
          "P",
          "Q",
          "E"
        ],
        "plane": "(NPQ)"
      }
    }
  },
  {
    "id": "mat-cau-cat-mat-phang",
    "slug": "sphere-secant-plane-intersection",
    "title": "Mặt cầu (S) cắt bởi mặt phẳng (P) theo giao tuyến đường tròn",
    "group": "Khối cong · cầu, trụ, nón",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "public",
    "problemText": "Trong không gian, cho mặt cầu (S) có tâm I(0; 0; 0) và bán kính R = 5. Mặt phẳng (P) song song với mặt phẳng Oxy, đi qua ba điểm M(4; 0; 3), N(0; 4; 3), K(-4; 0; 3) (có phương trình z - 3 = 0). Hạ IH vuông góc với mặt phẳng (P) tại H(0; 0; 3). Chứng minh d = IH = 3 < R = 5 nên mặt phẳng (P) cắt mặt cầu (S) theo đường tròn giao tuyến (C) tâm H, kiểm chứng IH ⊥ HM và tính bán kính r = √(R² - d²) = 4 cùng diện tích hình tròn thiết diện.",
    "description": "Trong không gian, cho mặt cầu (S) có tâm I(0; 0; 0) và bán kính R = 5. Mặt phẳng (P) song song với mặt phẳng Oxy, đi qua ba điểm M(4; 0; 3), N(0; 4; 3), K(-4; 0; 3) (có phương trình z - 3 = 0). Hạ IH vuông góc với mặt phẳng (P) tại H(0; 0; 3). Chứng minh d = IH = 3 < R = 5 nên mặt phẳng (P) cắt mặt cầu (S) theo đường tròn giao tuyến (C) tâm H, kiểm chứng IH ⊥ HM và tính bán kính r = √(R² - d²) = 4 cùng diện tích hình tròn thiết diện.",
    "stepCount": 7,
    "configHash": "81423f59a10cc397",
    "historyId": "h1a263u3",
    "solidFamily": "sphere",
    "illustration": {
      "mode": "verified",
      "family": "sphere",
      "templateId": "sphere.plane-section",
      "fallback": false,
      "labels": {
        "center": "I",
        "foot": "H",
        "rimPoint": "M",
        "plane": "(P)"
      }
    }
  },
  {
    "id": "oxyz-giao-diem-duong-mat",
    "slug": "oxyz-line-plane-intersection",
    "title": "Giao điểm M của đường thẳng d và mặt phẳng (P) trong Oxyz",
    "group": "Quan hệ song song – vuông góc",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "public",
    "problemText": "Trong không gian Oxyz, cho mặt phẳng (P) đi qua ba điểm A(6; 0; 0), B(0; 6; 0), C(0; 0; 6) có phương trình x + y + z - 6 = 0 và đường thẳng d đi qua hai điểm D(1; 1; 0), E(3; 3; 6). Xác định giao điểm duy nhất M = d ∩ (P), dựng hình chiếu vuông góc H của điểm E lên mặt phẳng (P) để biểu diễn góc cắt giữa d và (P), và tính khoảng cách từ gốc tọa độ O đến giao điểm M.",
    "description": "Trong không gian Oxyz, cho mặt phẳng (P) đi qua ba điểm A(6; 0; 0), B(0; 6; 0), C(0; 0; 6) có phương trình x + y + z - 6 = 0 và đường thẳng d đi qua hai điểm D(1; 1; 0), E(3; 3; 6). Xác định giao điểm duy nhất M = d ∩ (P), dựng hình chiếu vuông góc H của điểm E lên mặt phẳng (P) để biểu diễn góc cắt giữa d và (P), và tính khoảng cách từ gốc tọa độ O đến giao điểm M.",
    "stepCount": 7,
    "configHash": "9f2f78b5162e5c5d",
    "historyId": "h6o7gba",
    "solidFamily": "neutral",
    "illustration": {
      "mode": "verified",
      "family": "pyramid",
      "templateId": "oxyz.line-plane-intersection",
      "fallback": false,
      "labels": {
        "center": "O",
        "base": [
          "A",
          "B",
          "C"
        ],
        "foot": "M",
        "rimPoint": "H",
        "plane": "(P)"
      }
    }
  },
  {
    "id": "mat-phang-tiep-xuc-mat-cau",
    "slug": "sphere-tangent-plane-contact",
    "title": "Mặt phẳng tiếp diện (P) tiếp xúc với mặt cầu (S) tại tiếp điểm A",
    "group": "Khối cong · cầu, trụ, nón",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "public",
    "problemText": "Trong không gian Oxyz, cho mặt cầu (S) có tâm I(0; 0; 0), bán kính R = 5 và điểm A(3; 0; 4) thuộc mặt cầu (S). Dựng bán kính IA và mặt phẳng tiếp diện (P) đi qua A, vuông góc với bán kính IA (có phương trình 3x + 4z - 25 = 0). Lấy hai điểm B(3; 4; 4) và C(-1; 0; 7) trên tiếp diện (P), kiểm chứng IA ⊥ AB, IA ⊥ AC và d(I, (P)) = IA = R = 5 để khẳng định (P) tiếp xúc với mặt cầu (S) tại duy nhất tiếp điểm A.",
    "description": "Trong không gian Oxyz, cho mặt cầu (S) có tâm I(0; 0; 0), bán kính R = 5 và điểm A(3; 0; 4) thuộc mặt cầu (S). Dựng bán kính IA và mặt phẳng tiếp diện (P) đi qua A, vuông góc với bán kính IA (có phương trình 3x + 4z - 25 = 0). Lấy hai điểm B(3; 4; 4) và C(-1; 0; 7) trên tiếp diện (P), kiểm chứng IA ⊥ AB, IA ⊥ AC và d(I, (P)) = IA = R = 5 để khẳng định (P) tiếp xúc với mặt cầu (S) tại duy nhất tiếp điểm A.",
    "stepCount": 6,
    "configHash": "24dad93f7c5b8e36",
    "historyId": "hcy1pmd",
    "solidFamily": "sphere",
    "illustration": {
      "mode": "verified",
      "family": "sphere",
      "templateId": "sphere.tangent-plane",
      "fallback": false,
      "labels": {
        "center": "I",
        "rimPoint": "A",
        "secondRimPoint": "B"
      }
    }
  },
  {
    "id": "hinh-non-cat-song-song-day",
    "slug": "cone-parallel-base-section",
    "title": "Hình nón cắt bởi mặt phẳng (P) song song với mặt phẳng đáy",
    "group": "Khối cong · cầu, trụ, nón",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "public",
    "problemText": "Cho hình nón đỉnh S, tâm đáy O, bán kính đáy OA = R = 6 và chiều cao SO = h = 8. Mặt phẳng (P) đi qua trung điểm I của trục SO và song song với mặt phẳng đáy, cắt các đường sinh SA, SB lần lượt tại M, N và cắt hình nón theo đường tròn thiết diện (C) tâm I. Xác định tâm thiết diện I, điểm M trên đường sinh SA, dựng đường tròn thiết diện (C) và tính bán kính thiết diện r' = (SI/SO)·R = 3 cùng diện tích thiết diện.",
    "description": "Cho hình nón đỉnh S, tâm đáy O, bán kính đáy OA = R = 6 và chiều cao SO = h = 8. Mặt phẳng (P) đi qua trung điểm I của trục SO và song song với mặt phẳng đáy, cắt các đường sinh SA, SB lần lượt tại M, N và cắt hình nón theo đường tròn thiết diện (C) tâm I. Xác định tâm thiết diện I, điểm M trên đường sinh SA, dựng đường tròn thiết diện (C) và tính bán kính thiết diện r' = (SI/SO)·R = 3 cùng diện tích thiết diện.",
    "stepCount": 12,
    "configHash": "8340fcac79aefe15",
    "historyId": "h135atwl",
    "solidFamily": "cone",
    "illustration": {
      "mode": "verified",
      "family": "cone",
      "templateId": "cone.parallel-section",
      "fallback": false,
      "labels": {
        "apex": "S",
        "center": "O",
        "foot": "I",
        "rimPoint": "M",
        "secondRimPoint": "A"
      }
    }
  },
  {
    "id": "chop-mat-cau-ngoai-tiep",
    "slug": "pyramid-circumscribed-sphere",
    "title": "Hình chóp S.ABCD và mặt cầu ngoại tiếp (S) tâm I",
    "group": "Khối cong · cầu, trụ, nón",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "public",
    "problemText": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông tâm O cạnh bằng 4, cạnh bên SA vuông góc với mặt phẳng đáy (ABCD) và SA = 4. Dựng trục đường tròn ngoại tiếp đáy đi qua tâm O, dựng mặt phẳng trung trực của cạnh bên SA qua trung điểm M của SA để xác định tâm I của mặt cầu ngoại tiếp hình chóp S.ABCD. Kiểm chứng IA = IB = IC = ID = IS và tính bán kính R cùng thể tích khối cầu ngoại tiếp.",
    "description": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông tâm O cạnh bằng 4, cạnh bên SA vuông góc với mặt phẳng đáy (ABCD) và SA = 4. Dựng trục đường tròn ngoại tiếp đáy đi qua tâm O, dựng mặt phẳng trung trực của cạnh bên SA qua trung điểm M của SA để xác định tâm I của mặt cầu ngoại tiếp hình chóp S.ABCD. Kiểm chứng IA = IB = IC = ID = IS và tính bán kính R cùng thể tích khối cầu ngoại tiếp.",
    "stepCount": 17,
    "configHash": "29498ae479457796",
    "historyId": "h198csmj",
    "solidFamily": "pyramid",
    "illustration": {
      "mode": "verified",
      "family": "pyramid",
      "templateId": "pyramid.circumscribed-sphere",
      "fallback": false,
      "labels": {
        "apex": "S",
        "base": [
          "A",
          "B",
          "C",
          "D"
        ],
        "center": "I",
        "plane": "(α)"
      }
    }
  },
  {
    "id": "thiet-dien-chop",
    "slug": "pyramid-cross-section",
    "title": "Thiết diện của hình chóp cắt bởi mặt phẳng qua ba trung điểm",
    "group": "Dựng hình · thiết diện",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "internal_fixture",
    "problemText": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng đáy và SA = 4. Gọi M, N, P lần lượt là trung điểm của SA, SB, SC. Hãy dựng thiết diện của hình chóp khi cắt bởi mặt phẳng (MNP).",
    "description": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng đáy và SA = 4. Gọi M, N, P lần lượt là trung điểm của SA, SB, SC. Hãy dựng thiết diện của hình chóp khi cắt bởi mặt phẳng (MNP).",
    "stepCount": 10,
    "configHash": "ba0b7f4fb118a43f",
    "historyId": "h1v80xkc",
    "solidFamily": "pyramid",
    "illustration": {
      "mode": "verified",
      "family": "pyramid",
      "templateId": "pyramid.section",
      "fallback": false,
      "labels": {
        "apex": "S",
        "base": [
          "A",
          "B",
          "C",
          "D"
        ],
        "section": [
          "M",
          "N",
          "P",
          "Q"
        ],
        "plane": "(MNP)"
      }
    }
  },
  {
    "id": "mat-cheo-sac",
    "slug": "pyramid-diagonal-section",
    "title": "Thiết diện của hình chóp theo mặt phẳng chéo (SAC)",
    "group": "Dựng hình · thiết diện",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "internal_fixture",
    "problemText": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng đáy và SA = 4. Hãy dựng thiết diện của hình chóp khi cắt bởi mặt phẳng (SAC).",
    "description": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng đáy và SA = 4. Hãy dựng thiết diện của hình chóp khi cắt bởi mặt phẳng (SAC).",
    "stepCount": 6,
    "configHash": "890e51ba870a0b86",
    "historyId": "h3ztaqf",
    "solidFamily": "pyramid",
    "illustration": {
      "mode": "verified",
      "family": "pyramid",
      "templateId": "pyramid.diagonal-section",
      "fallback": false,
      "labels": {
        "apex": "S",
        "base": [
          "A",
          "B",
          "C",
          "D"
        ],
        "plane": "(SAC)"
      }
    }
  },
  {
    "id": "vuong-goc-chop",
    "slug": "pyramid-line-plane-angle",
    "title": "Đường thẳng vuông góc với mặt phẳng trong hình chóp",
    "group": "Quan hệ song song – vuông góc",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "internal_fixture",
    "problemText": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng đáy và SA = 4. Xét đường thẳng BC và mặt phẳng (SAB): hãy dựng hình rồi cho biết góc giữa chúng.",
    "description": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng đáy và SA = 4. Xét đường thẳng BC và mặt phẳng (SAB): hãy dựng hình rồi cho biết góc giữa chúng.",
    "stepCount": 5,
    "configHash": "3904300c35a48365",
    "historyId": "h1nu1huy",
    "solidFamily": "pyramid",
    "illustration": {
      "mode": "verified",
      "family": "pyramid",
      "templateId": "pyramid.perpendicular",
      "fallback": false,
      "labels": {
        "apex": "S",
        "base": [
          "A",
          "B",
          "C",
          "D"
        ],
        "plane": "(SAB)"
      }
    }
  },
  {
    "id": "mp-vuong-goc-duong",
    "slug": "pyramid-perpendicular-plane-distance",
    "title": "Mặt phẳng qua một điểm và vuông góc với đường thẳng cho trước",
    "group": "Quan hệ song song – vuông góc",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "internal_fixture",
    "problemText": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng đáy và SA = 4. Dựng mặt phẳng qua B và vuông góc với đường thẳng SC, rồi tính khoảng cách từ S đến mặt phẳng vừa dựng.",
    "description": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng đáy và SA = 4. Dựng mặt phẳng qua B và vuông góc với đường thẳng SC, rồi tính khoảng cách từ S đến mặt phẳng vừa dựng.",
    "stepCount": 7,
    "configHash": "c91607696fa0146a",
    "historyId": "h1pr6oq1",
    "solidFamily": "pyramid",
    "illustration": {
      "mode": "verified",
      "family": "pyramid",
      "templateId": "pyramid.altitude-distance",
      "fallback": false,
      "labels": {
        "apex": "S",
        "base": [
          "A",
          "B",
          "C",
          "D"
        ],
        "foot": "H",
        "plane": "(α)"
      }
    }
  },
  {
    "id": "the-tich-chop",
    "slug": "pyramid-volume-and-altitude",
    "title": "Thể tích khối chóp và khoảng cách từ đỉnh đến đáy",
    "group": "Khoảng cách · thể tích · góc",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "internal_fixture",
    "problemText": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng đáy và SA = 4. Tính thể tích khối chóp và khoảng cách từ S đến mặt phẳng đáy.",
    "description": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng đáy và SA = 4. Tính thể tích khối chóp và khoảng cách từ S đến mặt phẳng đáy.",
    "stepCount": 4,
    "configHash": "ff0bcc065348c835",
    "historyId": "h1edsyhc",
    "solidFamily": "pyramid",
    "illustration": {
      "mode": "verified",
      "family": "pyramid",
      "templateId": "pyramid.volume-height",
      "fallback": false,
      "labels": {
        "apex": "S",
        "base": [
          "A",
          "B",
          "C",
          "D"
        ]
      }
    }
  },
  {
    "id": "cau-the-tich",
    "slug": "sphere-radius-and-volume",
    "title": "Bán kính và thể tích khối cầu",
    "group": "Khối cong · cầu, trụ, nón",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "internal_fixture",
    "problemText": "Cho mặt cầu tâm I đi qua điểm A với IA = 3. Tính bán kính và thể tích khối cầu.",
    "description": "Cho mặt cầu tâm I đi qua điểm A với IA = 3. Tính bán kính và thể tích khối cầu.",
    "stepCount": 1,
    "configHash": "1bc33f3c73ad6764",
    "historyId": "h2gvfv3",
    "solidFamily": "sphere",
    "illustration": {
      "mode": "verified",
      "family": "sphere",
      "templateId": "sphere.basic-radius",
      "fallback": false,
      "labels": {
        "center": "I",
        "rimPoint": "A"
      }
    }
  },
  {
    "id": "cau-cat-mat-phang",
    "slug": "sphere-plane-intersection",
    "title": "Đường tròn giao của mặt phẳng và mặt cầu",
    "group": "Khối cong · cầu, trụ, nón",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "internal_fixture",
    "problemText": "Cho mặt cầu tâm I bán kính 5. Mặt phẳng (P) cách tâm I một khoảng bằng 3 cắt mặt cầu theo một đường tròn. Tính bán kính và diện tích hình tròn đó.",
    "description": "Cho mặt cầu tâm I bán kính 5. Mặt phẳng (P) cách tâm I một khoảng bằng 3 cắt mặt cầu theo một đường tròn. Tính bán kính và diện tích hình tròn đó.",
    "stepCount": 5,
    "configHash": "332e422272b4cbde",
    "historyId": "h1adcxcx",
    "solidFamily": "sphere",
    "illustration": {
      "mode": "verified",
      "family": "sphere",
      "templateId": "sphere.plane-section",
      "fallback": false,
      "labels": {
        "center": "I",
        "foot": "H",
        "rimPoint": "M",
        "plane": "(P)"
      }
    }
  },
  {
    "id": "tru-truc-xien",
    "slug": "tilted-right-cylinder-metrics",
    "title": "Hình trụ tròn xoay có trục đặt nghiêng",
    "group": "Khối cong · cầu, trụ, nón",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "internal_fixture",
    "problemText": "Cho hình trụ có hai tâm đáy là O và O′ với OO′ = 3, và một điểm A trên đường tròn đáy sao cho OA vuông góc với OO′ và OA = √5. Tính thể tích và diện tích xung quanh của hình trụ.",
    "description": "Cho hình trụ có hai tâm đáy là O và O′ với OO′ = 3, và một điểm A trên đường tròn đáy sao cho OA vuông góc với OO′ và OA = √5. Tính thể tích và diện tích xung quanh của hình trụ.",
    "stepCount": 3,
    "configHash": "6fcd193936264b8d",
    "historyId": "h1rt44b2",
    "solidFamily": "cylinder",
    "illustration": {
      "mode": "verified",
      "family": "cylinder",
      "templateId": "cylinder.oblique-axis",
      "fallback": false,
      "labels": {
        "center": "O",
        "topCenter": "O′",
        "rimPoint": "A"
      }
    }
  },
  {
    "id": "tru-thiet-dien-tron",
    "slug": "cylinder-perpendicular-section",
    "title": "Thiết diện vuông góc trục của hình trụ",
    "group": "Khối cong · cầu, trụ, nón",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "internal_fixture",
    "problemText": "Cho hình trụ có tâm hai đáy là O và O′, bán kính đáy bằng 2. Mặt phẳng đi qua trung điểm của OO′ và vuông góc với trục cắt hình trụ theo một đường tròn. Tính bán kính đường tròn ấy.",
    "description": "Cho hình trụ có tâm hai đáy là O và O′, bán kính đáy bằng 2. Mặt phẳng đi qua trung điểm của OO′ và vuông góc với trục cắt hình trụ theo một đường tròn. Tính bán kính đường tròn ấy.",
    "stepCount": 6,
    "configHash": "f1045cc865dfbd24",
    "historyId": "h1owk0zp",
    "solidFamily": "cylinder",
    "illustration": {
      "mode": "verified",
      "family": "cylinder",
      "templateId": "cylinder.perpendicular-section",
      "fallback": false,
      "labels": {
        "center": "O",
        "topCenter": "O′",
        "foot": "M",
        "plane": "(α)"
      }
    }
  },
  {
    "id": "non-duong-sinh",
    "slug": "cone-slant-height-and-surface",
    "title": "Đường sinh, thể tích và diện tích xung quanh hình nón",
    "group": "Khối cong · cầu, trụ, nón",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "internal_fixture",
    "problemText": "Cho hình nón có tâm đáy O, đỉnh S với SO = 4, và một điểm A trên đường tròn đáy với OA = 3. Tính độ dài đường sinh, thể tích và diện tích xung quanh của hình nón.",
    "description": "Cho hình nón có tâm đáy O, đỉnh S với SO = 4, và một điểm A trên đường tròn đáy với OA = 3. Tính độ dài đường sinh, thể tích và diện tích xung quanh của hình nón.",
    "stepCount": 4,
    "configHash": "cd80616245e496e8",
    "historyId": "h1wlf0au",
    "solidFamily": "cone",
    "illustration": {
      "mode": "verified",
      "family": "cone",
      "templateId": "cone.slant-generator",
      "fallback": false,
      "labels": {
        "apex": "S",
        "center": "O",
        "rimPoint": "A"
      }
    }
  },
  {
    "id": "non-thiet-dien-truc",
    "slug": "cone-axial-section",
    "title": "Thiết diện qua trục của hình nón",
    "group": "Khối cong · cầu, trụ, nón",
    "simId": "generic.semantic_program",
    "domain": "geometry",
    "visibility": "internal_fixture",
    "problemText": "Cho hình nón đỉnh S, tâm đáy O với SO = 4 và bán kính đáy bằng 3. Mặt phẳng đi qua trục cắt hình nón theo một tam giác. Tính diện tích thiết diện đó.",
    "description": "Cho hình nón đỉnh S, tâm đáy O với SO = 4 và bán kính đáy bằng 3. Mặt phẳng đi qua trục cắt hình nón theo một tam giác. Tính diện tích thiết diện đó.",
    "stepCount": 5,
    "configHash": "e1202141a682d0fe",
    "historyId": "hijp67n",
    "solidFamily": "cone",
    "illustration": {
      "mode": "verified",
      "family": "cone",
      "templateId": "cone.axial-section",
      "fallback": false,
      "labels": {
        "apex": "S",
        "center": "O",
        "rimPoint": "A",
        "secondRimPoint": "B"
      }
    }
  }
]);

export function configHashOf(env: Pick<SimulationEnvelope, "simulation_id" | "config">): string {
  const s = `${env.simulation_id}|${JSON.stringify(env.config)}`;
  let h1 = 0xdeadbeef;
  let h2 = 0x41c6ce57;
  for (let i = 0; i < s.length; i++) {
    const c = s.charCodeAt(i);
    h1 = Math.imul(h1 ^ c, 2654435761);
    h2 = Math.imul(h2 ^ c, 1597334677);
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
  return `${(h1 >>> 0).toString(16).padStart(8, "0")}${(h2 >>> 0).toString(16).padStart(8, "0")}`;
}

const _byId = new Map<string, SampleCatalogMeta>();
const _bySlug = new Map<string, SampleCatalogMeta>();
const _byConfigHash = new Map<string, SampleCatalogMeta>();
const _byHistoryId = new Map<string, SampleCatalogMeta>();
const _byNormStmt = new Map<string, SampleCatalogMeta>();

function normalizeStmtQuick(raw: string): string {
  return raw.normalize("NFC").replace(/\s+/gu, " ").trim();
}

for (const m of ALL_SAMPLE_META) {
  _byId.set(m.id, m);
  _bySlug.set(m.slug.toLowerCase(), m);
  _byConfigHash.set(m.configHash, m);
  if (!_byHistoryId.has(m.historyId)) _byHistoryId.set(m.historyId, m);
  const norm = normalizeStmtQuick(m.problemText);
  if (norm && !_byNormStmt.has(norm)) _byNormStmt.set(norm, m);
}

const _publicMeta = Object.freeze(
  ALL_SAMPLE_META.filter((m) => m.visibility === "public" && PRODUCT_DOMAINS.includes(m.domain)),
);
const _discoverableMeta = Object.freeze(
  ALL_SAMPLE_META.filter((m) => m.visibility === "public"),
);

export function offlineCatalogMeta(): readonly SampleCatalogMeta[] {
  return ALL_SAMPLE_META;
}

export function discoverableCatalogMeta(): readonly SampleCatalogMeta[] {
  return _discoverableMeta;
}

export function publicCatalogMeta(): readonly SampleCatalogMeta[] {
  return _publicMeta;
}

export function starterMetaEntries(): SampleCatalogMeta[] {
  const out: SampleCatalogMeta[] = [];
  for (const id of STARTER_SAMPLE_IDS) {
    const m = _byId.get(id);
    if (m && m.visibility === "public" && PRODUCT_DOMAINS.includes(m.domain)) out.push(m);
  }
  return out;
}

export function sampleMetaById(id: string | null | undefined): SampleCatalogMeta | undefined {
  if (!id) return undefined;
  return _byId.get(id) ?? _bySlug.get(id.toLowerCase());
}

export function sampleMetaByHistoryId(historyId: string | null | undefined): SampleCatalogMeta | undefined {
  if (!historyId) return undefined;
  return _byHistoryId.get(historyId);
}

export function sampleMetaByNormalizedStatement(norm: string | null | undefined): SampleCatalogMeta | undefined {
  if (!norm) return undefined;
  return _byNormStmt.get(norm);
}

export function canonicalSlugForSampleId(sampleIdOrToken: string): string {
  const trimmed = sampleIdOrToken.trim();
  if (!trimmed) return "";
  const direct = _byId.get(trimmed);
  if (direct) return direct.slug;
  const bySlug = _bySlug.get(trimmed.toLowerCase());
  if (bySlug) return bySlug.slug;
  return CANONICAL_SAMPLE_SLUGS[trimmed] ?? trimmed;
}

export function resolveSampleMetaByRouteToken(
  token: string | null | undefined,
): SampleCatalogMeta | undefined {
  if (!token) return undefined;
  const trimmed = token.trim();
  if (!trimmed) return undefined;
  const lower = trimmed.toLowerCase();
  const direct = _byId.get(trimmed) ?? _bySlug.get(lower);
  if (direct) return direct;
  return ALL_SAMPLE_META.find((m) => m.id.toLowerCase() === lower);
}

export function geometryShapeLabel(sampleId: string): string {
  const canonicalId = _bySlug.get(sampleId.toLowerCase())?.id ?? sampleId;
  if (canonicalId.startsWith("oxyz-")) {
    return "Tọa độ Oxyz";
  }
  if (
    canonicalId.startsWith("cau-") ||
    canonicalId.startsWith("mat-cau-") ||
    canonicalId === "mat-phang-tiep-xuc-mat-cau"
  ) {
    return "Mặt cầu";
  }
  if (
    canonicalId.startsWith("lap-phuong-") ||
    canonicalId.startsWith("lang-tru-")
  ) {
    return "Hình lăng trụ";
  }
  if (canonicalId.startsWith("tru-")) return "Hình trụ";
  if (
    canonicalId.startsWith("non-") ||
    canonicalId.startsWith("hinh-non-")
  ) {
    return "Hình nón";
  }
  return "Hình chóp";
}

export function problemTextForSample(sampleId: string): string {
  return resolveSampleMetaByRouteToken(sampleId)?.problemText ?? "";
}

export function resolveGeometrySampleIdMeta(
  target:
    | { id?: string | null; title?: string | null; envelope?: SimulationEnvelope | null }
    | null
    | undefined,
): string | null {
  if (!target) return null;
  if (target.id) {
    const byRoute = resolveSampleMetaByRouteToken(target.id);
    if (byRoute) return byRoute.id;
  }
  if (target.envelope) {
    const matched = _byConfigHash.get(configHashOf(target.envelope));
    if (matched) return matched.id;
  }
  return null;
}

export function geometryCategoryForItemMeta(
  target:
    | { id?: string | null; title?: string | null; envelope?: SimulationEnvelope | null }
    | null
    | undefined,
): Exclude<LibraryCategory, "all"> {
  const sampleId = resolveGeometrySampleIdMeta(target);
  if (sampleId) {
    return geometryShapeLabel(sampleId) as Exclude<LibraryCategory, "all">;
  }
  const text = `${target?.title ?? ""} ${target?.envelope?.title ?? ""}`.toLowerCase();
  if (text.includes("mặt cầu") || text.includes("khối cầu")) return "Mặt cầu";
  if (text.includes("lăng trụ") || text.includes("lập phương") || text.includes("hình hộp")) {
    return "Hình lăng trụ";
  }
  if (text.includes("hình trụ") || text.includes("khối trụ")) return "Hình trụ";
  if (text.includes("hình nón") || text.includes("khối nón")) return "Hình nón";
  if (text.includes("oxyz") && !text.includes("hình chóp") && !text.includes("tứ diện")) {
    return "Tọa độ Oxyz";
  }
  return "Hình chóp";
}

/** Đếm số bước nhẹ cho sidebar/danh sách mà không kéo `scene3d-semantic-policy.ts` hay `three`. */
export function stepCountOfEnvelopeLite(envelope: SimulationEnvelope): number {
  const matchedId = resolveGeometrySampleIdMeta({ envelope });
  if (matchedId) {
    const meta = _byId.get(matchedId);
    if (meta && meta.stepCount > 0) return meta.stepCount;
  }
  const scene3d = (envelope as { scene3d?: unknown }).scene3d;
  if (hopLeScene3D(scene3d)) {
    const count3d = geometryStepCount(scene3d);
    if (count3d > 0) return count3d;
  }
  const mod = getSimulation(envelope.simulation_id);
  if (mod?.timeline) {
    const check = mod.validateConfig(envelope.config);
    if (check.ok) {
      try {
        const total = mod.timeline.stepCount(mod.init(check.config));
        if (total > 0) return total;
      } catch {
        /* fallback bên dưới */
      }
    }
  }
  const cfg = envelope.config as { view_steps?: unknown[] } | null | undefined;
  if (cfg && Array.isArray(cfg.view_steps) && cfg.view_steps.length > 0) {
    return cfg.view_steps.length;
  }
  return 4;
}

export { historyIdOf };

/* ── Bộ nhớ đệm runtime theo nhu cầu (warm cache sau khi tải chunk bài mẫu) ─ */

const _payloadCacheById = new Map<string, CachedSampleRecord>();
const _payloadCacheByConfigHash = new Map<string, CachedSampleRecord>();

export function cacheSamplePayloads(entries: readonly CachedSampleRecord[]): void {
  for (const entry of entries) {
    _payloadCacheById.set(entry.id, entry);
    _payloadCacheByConfigHash.set(configHashOf(entry.envelope), entry);
  }
}

export function getCachedSampleEntry(idOrToken: string | null | undefined): CachedSampleRecord | null {
  if (!idOrToken) return null;
  const direct = _payloadCacheById.get(idOrToken);
  if (direct) return direct;
  const meta = resolveSampleMetaByRouteToken(idOrToken);
  return meta ? (_payloadCacheById.get(meta.id) ?? null) : null;
}

export function getCachedSampleEnvelope(idOrToken: string | null | undefined): SimulationEnvelope | null {
  return getCachedSampleEntry(idOrToken)?.envelope ?? null;
}

export function recoverCachedCatalogScene3D(env: SimulationEnvelope): SimulationEnvelope {
  const raw = env as SimulationEnvelope & { scene3d?: unknown };
  if (raw.scene3d !== undefined && raw.scene3d !== null) {
    return env;
  }
  const hit = _payloadCacheByConfigHash.get(configHashOf(env));
  if (hit) {
    const sampleScene = (hit.envelope as SimulationEnvelope & { scene3d?: unknown }).scene3d;
    if (sampleScene !== undefined && sampleScene !== null) {
      return { ...env, scene3d: sampleScene } as SimulationEnvelope;
    }
  }
  return env;
}
