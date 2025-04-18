import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AuthModalProvider } from '@/context/AuthModalContext';
import Navbar from '@/components/layout/Navbar'
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
  title: "Sprinter",
  description: "Sprinter is an AI powered Education Platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <AuthModalProvider>
          <Navbar/>
          {children}
        </AuthModalProvider>
      </body>
    </html>
  );
}
