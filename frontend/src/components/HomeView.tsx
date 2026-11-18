import { ProblemInput } from "./ProblemInput";

export function HomeView() {
  return (
    <main
      className="home-container is-minimal-home"
      id="view-home"
      aria-label="Màn hình nhập đề toán"
    >
      <div className="home-hero">
        <h1 className="hero-title home-hero-title">Em muốn dựng hình nào?</h1>

        <div className="home-composer" aria-label="Khung nhập đề toán">
          <ProblemInput />
        </div>
      </div>
    </main>
  );
}
