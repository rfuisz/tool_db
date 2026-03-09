import type { Metadata } from "next";
import { EB_Garamond, Jost, Inter, JetBrains_Mono } from "next/font/google";
import { DeploymentBadge } from "@/components/deployment-badge";
import { Nav } from "@/components/nav";
import { PaperModalProvider } from "@/components/paper-modal";
import { isFirstPassEnabled } from "@/lib/first-pass-access";
import "./globals.css";

const ebGaramond = EB_Garamond({
  variable: "--font-eb-garamond",
  subsets: ["latin"],
  display: "swap",
});

const jost = Jost({
  variable: "--font-jost",
  subsets: ["latin"],
  display: "swap",
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "BioControl Toolkit DB",
  description:
    "Evidence-first engineering knowledge system for biological control surfaces, methods, and DBTL workflows.",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const showFirstPass = await isFirstPassEnabled();

  return (
    <html
      lang="en"
      className={`${ebGaramond.variable} ${jost.variable} ${inter.variable} ${jetbrains.variable}`}
    >
      <body className="min-h-screen">
        <PaperModalProvider>
          <Nav showFirstPass={showFirstPass} />
          <main className="mx-auto max-w-5xl px-6 pt-24 pb-24">{children}</main>
          <footer className="border-t border-edge bg-surface/40">
            <div className="mx-auto max-w-5xl px-6 py-12">
              <blockquote className="max-w-3xl font-body text-[15px] leading-8 text-ink-secondary italic">
                <p>
                  &ldquo;They always talked of being reincarnated so that they
                  could kiss in public. They died together, in an accident,
                  during a clandestine encounter. He was reincarnated as a
                  circus elephant and she as a petunia. The life of a petunia
                  is very brief, which put them out of sync. In the following
                  reincarnation, both were human, with sixty-three years
                  between them. She became Pope and he a darling little girl
                  who was permitted to kiss the papal ring during an
                  audience.&rdquo;
                </p>
              </blockquote>
              <p className="small-caps mt-3 text-ink-muted">
                Ana Maria Shua
              </p>
              <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2 font-ui text-sm text-ink-muted">
                <a
                  href="https://twitter.com/richardfuisz"
                  target="_blank"
                  rel="noreferrer"
                  className="transition-colors hover:text-accent"
                >
                  @richardfuisz
                </a>
                <a
                  href="https://fuisz.xyz"
                  target="_blank"
                  rel="noreferrer"
                  className="transition-colors hover:text-accent"
                >
                  fuisz.xyz
                </a>
              </div>
              <div className="mt-6">
                <DeploymentBadge />
              </div>
            </div>
          </footer>
        </PaperModalProvider>
      </body>
    </html>
  );
}
