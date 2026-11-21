import { LandingAboutAxo } from "./landing/LandingAboutAxo";
import { LandingFooter } from "./landing/LandingFooter";
import { LandingHeader } from "./landing/LandingHeader";
import { LandingHeroV14 } from "./landing/LandingHeroV14";
import { LandingHowItWorks } from "./landing/LandingHowItWorks";
import { LandingSamples } from "./landing/LandingSamples";

export function LandingView() {
  return (
    <div id="view-landing" className="axo-sp-root axo-v14-root">
      <LandingHeader />
      <main id="landing-main" className="axo-sp-main axo-v14-main">
        <LandingHeroV14 />
        <LandingAboutAxo />
        <LandingHowItWorks />
        <LandingSamples />
      </main>
      <LandingFooter />
    </div>
  );
}
