import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "OpsNexus",
  description: "Autonomous document intake and resolution for B2B back-office operations.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      {/*
        suppressHydrationWarning: browser extensions (Grammarly, ColorZilla, etc.)
        inject attributes like data-gr-ext-installed / cz-shortcut-listen into body
        before React hydrates. That's a client-only DOM mutation outside our
        control, not a real SSR/CSR mismatch -- this only silences the attribute
        diff on this element, children still warn normally.
      */}
      <body className="min-h-full flex flex-col" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
