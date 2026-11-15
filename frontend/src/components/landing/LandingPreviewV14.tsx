import { LandingClosingV14, LandingFooterV14 } from "./LandingClosingV14";
import { LandingHeader } from "./LandingHeader";
import { LandingHeroV14 } from "./LandingHeroV14";
import { LandingInteractiveDemo } from "./LandingInteractiveDemo";
import { LandingStorytellingV14 } from "./LandingStorytellingV14";

export function LandingPreviewV14() {
  return (
    <div id="view-landing" className="axo-sp-root axo-v14-root">
      <LandingHeader />
      <main id="landing-main" className="axo-sp-main axo-v14-main">
        <LandingHeroV14 />
        <LandingStorytellingV14 />
        <LandingInteractiveDemo presentation="v14" />
        <LandingClosingV14 />
      </main>
      <LandingFooterV14 />
    </div>
  );
}
