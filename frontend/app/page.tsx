import { SiteHeader } from "@/components/site-header";
import { Hero } from "@/components/hero";
import { HowItWorks } from "@/components/how-it-works";
import { FeatureShowcase } from "@/components/feature-showcase";
import { CtaSection } from "@/components/cta-section";
import { SiteFooter } from "@/components/site-footer";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-paper dark:bg-paper-dark">
      <SiteHeader />
      <Hero />
      <HowItWorks />
      <FeatureShowcase />
      <CtaSection />
      <SiteFooter />
    </main>
  );
}
