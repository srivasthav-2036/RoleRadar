import type { Metadata } from "next";
import { Space_Grotesk, Inter, JetBrains_Mono } from "next/font/google";
import { ThemeProvider } from "@/components/theme-provider";
import { AuthProvider } from "@/lib/auth-context";
import { NavigationProgress } from "@/components/navigation-loading";
import { NavigationLoadingProvider } from "@/lib/navigation-context";
import { PipelineStatusProvider } from "@/lib/pipeline-status-context";
import "./globals.css";

const display = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "600"],
});

const body = Inter({
  subsets: ["latin"],
  variable: "--font-body",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "RoleRadar — Job matches you don't have to look for",
  description:
    "RoleRadar reads your resume, scores every open role against it, and tailors your resume for the ones worth applying to.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} ${mono.variable}`} suppressHydrationWarning>
      <body className="font-body">
        <ThemeProvider>
          <AuthProvider>
            <NavigationLoadingProvider>
              <PipelineStatusProvider>
                <NavigationProgress />
                {children}
              </PipelineStatusProvider>
            </NavigationLoadingProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

