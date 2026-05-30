import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { Toaster } from "react-hot-toast";
import QueryProvider from "@/components/providers/QueryProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CS Platform — AI-Powered Customer Service",
  description:
    "AI-powered customer service intelligence platform with chatbot, workflow automation, and analytics.",
};

import { ThemeProvider } from "@/components/providers/ThemeProvider";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className} suppressHydrationWarning>
        <ThemeProvider>
          <QueryProvider>
            <AuthProvider>
              {children}
              <Toaster
                position="top-right"
                toastOptions={{
                  style: {
                    background: "#1e1b4b",
                    color: "#e0e7ff",
                    border: "1px solid #4f46e5",
                  },
                }}
              />
            </AuthProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
