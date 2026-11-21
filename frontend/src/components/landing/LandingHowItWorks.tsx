import { useLandingReveal } from "./useLandingReveal";

export function LandingHowItWorks() {
  const { ref, revealState } = useLandingReveal<HTMLDivElement>();

  return (
    <section
      id="cach-hoat-dong"
      className="axo-how"
      aria-labelledby="axo-how-heading"
    >
      <div ref={ref} className="axo-how-shell" data-reveal={revealState}>
        <div className="axo-how-header">
          <h2 id="axo-how-heading" className="axo-how-title">
            Từ câu đề đến mô hình 3D.
          </h2>
          <p className="axo-how-lead">
            Ba bước ngắn gọn trong Workspace để đi thẳng từ câu đề tiếng Việt
            tới mô hình 3D trực quan.
          </p>
        </div>

        <div className="axo-how-steps">
          <article className="axo-how-step">
            <div className="axo-how-visual" data-ui="true">
              <div className="axo-how-composer-mock" aria-hidden="true">
                <div className="axo-how-composer-box">
                  <p className="axo-how-composer-text">
                    Cho hình chóp S.ABCD có đáy hình vuông tâm O, SA ⊥ (ABCD). Dựng thiết diện (MNP)...
                  </p>
                  <div className="axo-how-composer-foot">
                    <div className="axo-how-composer-chips">
                      <span className="axo-how-composer-chip">Thiết diện chóp</span>
                      <span className="axo-how-composer-chip">Mặt cầu ngoại tiếp</span>
                    </div>
                    <span className="axo-how-composer-send">
                      <svg
                        width="13"
                        height="13"
                        viewBox="0 0 16 16"
                        fill="none"
                        aria-hidden="true"
                        focusable="false"
                      >
                        <path
                          d="M8 12.5V3.5M8 3.5L4.25 7.25M8 3.5L11.75 7.25"
                          stroke="currentColor"
                          strokeWidth="1.8"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <div className="axo-how-step-body">
              <h3 className="axo-how-point-title">Nhập đề bài hoặc mở bài mẫu</h3>
              <p className="axo-how-point-desc">
                Gõ đề tiếng Việt trong khung hội thoại hoặc chọn nhanh ví dụ có sẵn.
              </p>
            </div>
          </article>

          <article className="axo-how-step">
            <div className="axo-how-visual">
              <img
                src="/assets/landing/product-renders/how-step-construct.png"
                width={920}
                height={642}
                alt="Bước dựng trung gian hình chóp S.ABCD với đường cao SA vuông góc đáy và ba trung điểm M, N, P trong Axo Workspace"
                loading="lazy"
                decoding="async"
                draggable={false}
                className="axo-how-step-img"
              />
            </div>
            <div className="axo-how-step-body">
              <h3 className="axo-how-point-title">Hệ thống dựng mô hình hình học</h3>
              <p className="axo-how-point-desc">
                Xác định hình khối, quan hệ vuông góc và vị trí từng điểm dựng.
              </p>
            </div>
          </article>

          <article className="axo-how-step">
            <div className="axo-how-visual">
              <img
                src="/assets/landing/product-renders/how-step-inspect.png"
                width={920}
                height={642}
                alt="Cùng mô hình hình chóp S.ABCD hoàn thiện thiết diện ngũ giác M-E-N-P-F ở góc xoay 3D và chế độ nhìn xuyên thấu trong Axo Workspace"
                loading="lazy"
                decoding="async"
                draggable={false}
                className="axo-how-step-img"
              />
            </div>
            <div className="axo-how-step-body">
              <h3 className="axo-how-point-title">Quan sát và tương tác 3D</h3>
              <p className="axo-how-point-desc">
                Xoay góc nhìn, bật xuyên thấu để theo dõi thiết diện bên trong khối.
              </p>
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}
