import type { Metadata } from "next";
import { EB_Garamond, Jost, Inter, JetBrains_Mono } from "next/font/google";
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
      <body>
        <PaperModalProvider>
          <Nav showFirstPass={showFirstPass} />
          <main className="mx-auto max-w-5xl px-6 pt-24 pb-24">{children}</main>
        </PaperModalProvider>
      </body>
    </html>
  );
}
