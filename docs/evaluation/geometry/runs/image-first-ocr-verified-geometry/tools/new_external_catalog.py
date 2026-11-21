# -*- coding: utf-8 -*-
"""Catalog 12 ảnh đề toán thực tế chưa từng dùng (unseen external images) từ `anvo25/vmmu` (MIT License)
cho run `image-first-ocr-verified-geometry`.

Gồm:
- 5 ảnh hình học không gian đa diện thuộc phạm vi hỗ trợ (`r313`, `r351`, `r387`, `r403`, `r411` từ `full_vqa`)
- 3 ảnh hình học không gian mặt tròn xoay ngoài phạm vi Kernel đa diện (`r395`, `r412`, `r424` từ `full_vqa`)
- 4 ảnh hình học phẳng / tối ưu thực tế / bảng biến thiên (`r18`, `r21`, `r31`, `r3` từ `random_subset_ocr` có
  văn bản chuẩn của tác giả trong `cropped_random_subset_vqa_description`)
"""
from __future__ import annotations

from typing import Any

NEW_EXTERNAL_ITEMS: list[dict[str, Any]] = [
    {
        "image_id": "new_ext_01_vmmu_full_r313",
        "filename": "vmmu_full_r313_Math_0311_test_062_question_30_page_3_key_A_vqa.png",
        "source_url": "https://huggingface.co/datasets/anvo25/vmmu",
        "original_image_url": "https://datasets-server.huggingface.co/rows?dataset=anvo25/vmmu&config=default&split=full_vqa&offset=313&length=1",
        "license_status": "MIT",
        "original_file_sha256": "18c0f3184ce216a897f0265b63be9e338bf0ec5b754b156fc9b80328cebbeaef",
        "printed_or_handwritten": "PRINTED",
        "has_complete_problem": True,
        "has_geometry_diagram": True,
        "diagram_embedded_facts": [],
        "ground_truth_verification_status": "GROUND_TRUTH_UNVERIFIED",
        "data_partition": "independent_holdout",
        "ground_truth_text": (
            "Câu 30. Cho hình chóp S.ABC có SA vuông góc với mặt phẳng (ABC), ΔABC là tam giác đều cạnh bằng a, "
            "SA = 2a (tham khảo hình vẽ bên dưới).\n"
            "Khoảng cách từ A đến mặt phẳng (SBC) bằng\n"
            "A. 2√57a/19. B. √57a/6. C. √57a/3. D. √57a/19."
        ),
    },
    {
        "image_id": "new_ext_02_vmmu_full_r351",
        "filename": "vmmu_full_r351_Math_0287_test_053_question_18_page_2_key_B_vqa.png",
        "source_url": "https://huggingface.co/datasets/anvo25/vmmu",
        "original_image_url": "https://datasets-server.huggingface.co/rows?dataset=anvo25/vmmu&config=default&split=full_vqa&offset=351&length=1",
        "license_status": "MIT",
        "original_file_sha256": "4ba88cdcc4b32c57bad80b721cd4b993ae7ae498bad13bfb330eaf7d6f52508a",
        "printed_or_handwritten": "PRINTED",
        "has_complete_problem": True,
        "has_geometry_diagram": True,
        "diagram_embedded_facts": [],
        "ground_truth_verification_status": "GROUND_TRUTH_UNVERIFIED",
        "data_partition": "independent_holdout",
        "ground_truth_text": (
            "Câu 18. Cho hình lập phương ABCD.A'B'C'D' (tham khảo hình bên).\n"
            "Xác định góc giữa hai đường thẳng A'D và A'B.\n"
            "A. 45°. B. 60°. C. 90°. D. 30°."
        ),
    },
    {
        "image_id": "new_ext_03_vmmu_full_r387",
        "filename": "vmmu_full_r387_Math_0321_test_063_question_43_page_5_key_D_vqa.png",
        "source_url": "https://huggingface.co/datasets/anvo25/vmmu",
        "original_image_url": "https://datasets-server.huggingface.co/rows?dataset=anvo25/vmmu&config=default&split=full_vqa&offset=387&length=1",
        "license_status": "MIT",
        "original_file_sha256": "4404f15670d101e7eceaab75f2980340b747cdc93a64a75757d88f308abce934",
        "printed_or_handwritten": "PRINTED",
        "has_complete_problem": True,
        "has_geometry_diagram": True,
        "diagram_embedded_facts": [],
        "ground_truth_verification_status": "GROUND_TRUTH_UNVERIFIED",
        "data_partition": "independent_holdout",
        "ground_truth_text": (
            "Câu 43. Cho hình lăng trụ đứng ABC.A'B'C' có tất cả các cạnh bằng a. Gọi M là trung điểm của CC' "
            "(tham khảo hình bên). Khoảng cách từ M đến mặt phẳng (A'BC) bằng\n"
            "A. √21a/7. B. √2a/2. C. √2a/4. D. √21a/14."
        ),
    },
    {
        "image_id": "new_ext_04_vmmu_full_r403",
        "filename": "vmmu_full_r403_Math_0312_test_062_question_32_page_4_key_D_vqa.png",
        "source_url": "https://huggingface.co/datasets/anvo25/vmmu",
        "original_image_url": "https://datasets-server.huggingface.co/rows?dataset=anvo25/vmmu&config=default&split=full_vqa&offset=403&length=1",
        "license_status": "MIT",
        "original_file_sha256": "ad2a92857d6d81e40c602b58b874d4ecf017af8773c12f7440503764826570f4",
        "printed_or_handwritten": "PRINTED",
        "has_complete_problem": True,
        "has_geometry_diagram": True,
        "diagram_embedded_facts": [],
        "ground_truth_verification_status": "GROUND_TRUTH_UNVERIFIED",
        "data_partition": "independent_holdout",
        "ground_truth_text": (
            "Câu 32. Cho hình chóp S.ABCD có tất cả các cạnh đều bằng a. Gọi M và N lần lượt là trung điểm của SC và BC "
            "(tham khảo hình vẽ bên dưới).\n"
            "Số đo của góc giữa hai đường thẳng MN và CD bằng\n"
            "A. 90°. B. 30°. C. 45°. D. 60°."
        ),
    },
    {
        "image_id": "new_ext_05_vmmu_full_r411",
        "filename": "vmmu_full_r411_Math_0133_test_023_question_35_page_5_key_B_vqa.png",
        "source_url": "https://huggingface.co/datasets/anvo25/vmmu",
        "original_image_url": "https://datasets-server.huggingface.co/rows?dataset=anvo25/vmmu&config=default&split=full_vqa&offset=411&length=1",
        "license_status": "MIT",
        "original_file_sha256": "6751cfe07bfaaf1236258df5b7d8c6700901efb0750961b1fc45817af4e48bb7",
        "printed_or_handwritten": "PRINTED",
        "has_complete_problem": True,
        "has_geometry_diagram": True,
        "diagram_embedded_facts": [],
        "ground_truth_verification_status": "GROUND_TRUTH_UNVERIFIED",
        "data_partition": "independent_holdout",
        "ground_truth_text": (
            "Câu 35 (VD) Cho hình chóp S.ABC có SA vuông góc với mặt phẳng (ABC), SA = √2a, tam giác ABC vuông cân tại B "
            "và AC = 2a (minh họa như hình bên). Góc giữa đường thẳng SB và mặt phẳng (ABC) bằng\n"
            "A. 30°. B. 45°. C. 60°. D. 90°."
        ),
    },
    {
        "image_id": "new_ext_06_vmmu_full_r395",
        "filename": "vmmu_full_r395_Math_0006_test_001_question_48_page_6_key_A_vqa.png",
        "source_url": "https://huggingface.co/datasets/anvo25/vmmu",
        "original_image_url": "https://datasets-server.huggingface.co/rows?dataset=anvo25/vmmu&config=default&split=full_vqa&offset=395&length=1",
        "license_status": "MIT",
        "original_file_sha256": "b338bf8dd719bb5026a7732b35f1e8282e3510498da77a13d4a314394b895df8",
        "printed_or_handwritten": "PRINTED",
        "has_complete_problem": True,
        "has_geometry_diagram": True,
        "diagram_embedded_facts": [],
        "ground_truth_verification_status": "GROUND_TRUTH_UNVERIFIED",
        "data_partition": "independent_holdout",
        "ground_truth_text": (
            "Câu 48: Có một cốc thủy tinh hình trụ, bán kính trong lòng đáy cốc là 4cm, chiều cao trong lòng cốc là "
            "10cm đang đựng một lượng nước. Tính thể tích nước trong cốc. biết khi nghiêng cốc nước vừa lúc nước "
            "chạm miệng cốc thì ở đáy mực nước trùng với đường kính đáy\n"
            "A. 320/3 cm³. B. 320/3 πcm³. C. 160/3 πcm³. D. 160/3 cm³."
        ),
    },
    {
        "image_id": "new_ext_07_vmmu_full_r412",
        "filename": "vmmu_full_r412_Math_0367_test_071_question_37_page_4_key_A_vqa.png",
        "source_url": "https://huggingface.co/datasets/anvo25/vmmu",
        "original_image_url": "https://datasets-server.huggingface.co/rows?dataset=anvo25/vmmu&config=default&split=full_vqa&offset=412&length=1",
        "license_status": "MIT",
        "original_file_sha256": "f219bdbecc55bb1b85eed270205ed69275dfa1e01a70473b713db1a3a080fc06",
        "printed_or_handwritten": "PRINTED",
        "has_complete_problem": True,
        "has_geometry_diagram": True,
        "diagram_embedded_facts": [],
        "ground_truth_verification_status": "GROUND_TRUTH_UNVERIFIED",
        "data_partition": "independent_holdout",
        "ground_truth_text": (
            "Câu 37. Trên bàn có một cốc nước hình trụ chứa đầy nước, có chiều cao bằng 3 lần đường kính của đáy, "
            "một viên bi và một khối nón đều bằng thủy tinh. Biết viên bi là một khối cầu có đường kính bằng đường kính "
            "phía trong của cốc nước. Người ta từ từ thả vào cốc nước viên bi và khối nón đó (như hình vẽ) thì thấy "
            "nước trong cốc tràn ra ngoài. Tính tỉ số thể tích của lượng nước còn lại trong cốc và lượng nước ban đầu "
            "(bỏ qua bề dày của lớp vỏ thủy tinh).\n"
            "A. 5/9 B. 1/2 C. 4/9 D. 2/3"
        ),
    },
    {
        "image_id": "new_ext_08_vmmu_full_r424",
        "filename": "vmmu_full_r424_Math_0371_test_073_question_38_page_4_key_B_vqa.png",
        "source_url": "https://huggingface.co/datasets/anvo25/vmmu",
        "original_image_url": "https://datasets-server.huggingface.co/rows?dataset=anvo25/vmmu&config=default&split=full_vqa&offset=424&length=1",
        "license_status": "MIT",
        "original_file_sha256": "a2bbfb46bee67f003d8a01532438497d46ba6e3d3f982f5d3bec5744dff3f031",
        "printed_or_handwritten": "PRINTED",
        "has_complete_problem": True,
        "has_geometry_diagram": True,
        "diagram_embedded_facts": [],
        "ground_truth_verification_status": "GROUND_TRUTH_UNVERIFIED",
        "data_partition": "independent_holdout",
        "ground_truth_text": (
            "Câu 38: Cho hình trụ có bán kính đáy bằng 2. Cắt hình trụ bởi một mặt phẳng (P) song song và cách trục "
            "của hình trụ một khoảng bằng √3, ta được thiết diện là một hình vuông. Gọi S₁, S₂ (S₁ < S₂) lần lượt là "
            "diện tích xung quanh của hai phần hình trụ được cắt ra. Tính S₁.\n"
            "A. S₁ = 3/4 π. B. S₁ = 4/3 π. C. S₁ = 5/3 π. D. S₁ = 20/3 π."
        ),
    },
    {
        "image_id": "new_ext_09_vmmu_ocr_r18",
        "filename": "vmmu_new_r18_Math_0252_test_046_question_31_page_4_key_B_vqa.png",
        "source_url": "https://huggingface.co/datasets/anvo25/vmmu",
        "original_image_url": "https://datasets-server.huggingface.co/rows?dataset=anvo25/vmmu&config=default&split=random_subset_ocr&offset=18&length=1",
        "license_status": "MIT",
        "original_file_sha256": "4ddb5f32a950fab6715ae2281ae58ab03729be3fbff39353be1d6c2f9589d230",
        "printed_or_handwritten": "PRINTED",
        "has_complete_problem": True,
        "has_geometry_diagram": True,
        "diagram_embedded_facts": [],
        "ground_truth_verification_status": "AUTHOR_PROVIDED_VMMU_DESCRIPTION",
        "data_partition": "independent_holdout",
        "ground_truth_text": (
            "Câu 31. Người ta muốn trồng hoa trên một miếng đất hình tròn có bán kính bằng 5 m. Họ dự định sẽ để lại "
            "một phần (phần màu trắng như hình vẽ, trong đó AB = 6 m) để làm việc khác. Biết mỗi mét vuông trồng hoa "
            "cần chi phí 200 nghìn đồng. Hỏi cần bao nhiêu tiền để có thể thực hiện dự định này?\n"
            "A. 22335 nghìn đồng. B. 14890 nghìn đồng. C. 7445 nghìn đồng. D. 3723 nghìn đồng."
        ),
    },
    {
        "image_id": "new_ext_10_vmmu_ocr_r21",
        "filename": "vmmu_new_r21_Math_0410_test_083_question_44_page_5_key_C_vqa.png",
        "source_url": "https://huggingface.co/datasets/anvo25/vmmu",
        "original_image_url": "https://datasets-server.huggingface.co/rows?dataset=anvo25/vmmu&config=default&split=random_subset_ocr&offset=21&length=1",
        "license_status": "MIT",
        "original_file_sha256": "61b1c0d49e77a25b3276198a9f7d8aad2f08a6b9b30e887f0e368f5095b6129a",
        "printed_or_handwritten": "PRINTED",
        "has_complete_problem": True,
        "has_geometry_diagram": True,
        "diagram_embedded_facts": [],
        "ground_truth_verification_status": "AUTHOR_PROVIDED_VMMU_DESCRIPTION",
        "data_partition": "independent_holdout",
        "ground_truth_text": (
            "Câu 44. Một sợi dây kim loại dài 120cm được cắt thành hai đoạn. Đoạn dây thứ nhất được uốn thành hình vuông, "
            "đoạn dây thứ hai được uốn thành vòng tròn (tham khảo hình bên dưới).\n"
            "Tổng diện tích của hình vuông và hình tròn đạt giá trị nhỏ nhất là (làm tròn đến hàng đơn vị)\n"
            "A. 498. B. 462. C. 504. D. 426."
        ),
    },
    {
        "image_id": "new_ext_11_vmmu_ocr_r31",
        "filename": "vmmu_new_r31_Math_0400_test_080_question_44_page_6_key_C_vqa.png",
        "source_url": "https://huggingface.co/datasets/anvo25/vmmu",
        "original_image_url": "https://datasets-server.huggingface.co/rows?dataset=anvo25/vmmu&config=default&split=random_subset_ocr&offset=31&length=1",
        "license_status": "MIT",
        "original_file_sha256": "67f9e1ea363296d006ce9c82e3210cabb42654f6aaeeec07e784526f04dae73b",
        "printed_or_handwritten": "PRINTED",
        "has_complete_problem": True,
        "has_geometry_diagram": True,
        "diagram_embedded_facts": ["ABCD_RECTANGLE_PLUS_SEMICIRCLE_WINDOW", "r_SEMICIRCLE_RADIUS", "h_RECTANGLE_HEIGHT"],
        "ground_truth_verification_status": "AUTHOR_PROVIDED_VMMU_DESCRIPTION",
        "data_partition": "independent_holdout",
        "ground_truth_text": (
            "Câu 44: Bác thợ hàn dùng một thanh kim loại dài 4 m để uốn thành khung cửa sổ có dạng như hình vẽ. "
            "Gọi r là bán kính của nửa đường tròn, tìm r (theo mét) để diện tích tạo thành đạt giá trị lớn nhất.\n"
            "A. 1 m. B. 0,5 m. C. 4/(π+4) m. D. 2/(4+π) m."
        ),
    },
    {
        "image_id": "new_ext_12_vmmu_ocr_r3",
        "filename": "vmmu_new_r3_Math_0001_test_001_question_9_page_1_key_D_vqa.png",
        "source_url": "https://huggingface.co/datasets/anvo25/vmmu",
        "original_image_url": "https://datasets-server.huggingface.co/rows?dataset=anvo25/vmmu&config=default&split=random_subset_ocr&offset=3&length=1",
        "license_status": "MIT",
        "original_file_sha256": "242fa4d95e261e7e320dc48ebfee622d6b60e8c0f43e4c9552ad40a8191901ec",
        "printed_or_handwritten": "PRINTED",
        "has_complete_problem": True,
        "has_geometry_diagram": False,
        "diagram_embedded_facts": ["VARIATION_TABLE_VALUES"],
        "ground_truth_verification_status": "AUTHOR_PROVIDED_VMMU_DESCRIPTION",
        "data_partition": "independent_holdout",
        "ground_truth_text": (
            "Câu 9: Cho hàm số y = f(x) có bảng biến thiên như hình sau:\n"
            "Hàm số y = f(x) đồng biến trên khoảng nào dưới đây?\n"
            "A. (-∞;0). B. (-2;2). C. (-1;3). D. (-∞;-2)."
        ),
    },
]
