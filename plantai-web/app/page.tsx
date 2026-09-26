import { CTA } from "@/components/landing/CTA";
import { DiagnosisSection } from "@/components/landing/DiagnosisSection";
import { EvidenceSection } from "@/components/landing/EvidenceSection";
import { Footer } from "@/components/landing/Footer";
import { Hero } from "@/components/landing/Hero";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { Navbar } from "@/components/landing/Navbar";
import { TreatmentSection } from "@/components/landing/TreatmentSection";

export default function Home() {
  return (
    <main className="overflow-hidden">
      <Navbar />
      <Hero />
      <HowItWorks />
      <DiagnosisSection />
      <EvidenceSection />
      <TreatmentSection />
      <CTA />
      <Footer />
    </main>
  );
}
