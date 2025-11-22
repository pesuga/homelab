import GridShape from "@/components/common/GridShape";
import ThemeTogglerTwo from "@/components/common/ThemeTogglerTwo";

import { ThemeProvider } from "@/context/ThemeContext";
import Image from "next/image";
import Link from "next/link";
import React from "react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative p-6 bg-white z-1 dark:bg-gray-900 sm:p-0">
      <ThemeProvider>
        <div className="relative flex lg:flex-row w-full h-screen justify-center flex-col  dark:bg-gray-900 sm:p-0">
          {children}
          <div className="lg:w-1/2 w-full h-full bg-brand-950 dark:bg-white/5 lg:grid items-center hidden">
            <div className="relative items-center justify-center  flex z-1">
              {/* <!-- ===== Common Grid Shape Start ===== --> */}
              <GridShape />
              <div className="flex flex-col items-center max-w-xs">
                <Link href="/" className="block mb-6">
                  <div className="flex items-center gap-3">
                    <svg
                      className="fill-current text-blue-600"
                      width="48"
                      height="48"
                      viewBox="0 0 32 32"
                      fill="none"
                    >
                      <path d="M16 4C12.8 4 10 5.6 8.4 8.4C6.8 6.8 4.4 6 2 6V8C4 8 6 8.8 7.2 10.4C6.4 12.4 6 14.4 6 16.4C6 23.2 11.2 28.4 18 28.4C24.8 28.4 30 23.2 30 16.4C30 9.6 24.8 4.4 18 4.4H16V4ZM16 6.4H18C23.6 6.4 28 10.8 28 16.4C28 22 23.6 26.4 18 26.4C12.4 26.4 8 22 8 16.4C8 14.8 8.4 13.2 9.2 11.6C10.8 13.6 13.2 14.8 16 14.8V12.8C13.6 12.8 11.6 11.6 10.4 9.6C12 7.6 14 6.4 16 6.4Z" />
                    </svg>
                    <span className="text-3xl font-bold text-white dark:text-white">
                      Family Assistant
                    </span>
                  </div>
                </Link>
                <p className="text-center text-gray-400 dark:text-white/60">
                  Your AI-powered family companion for managing memories, schedules, and knowledge
                </p>
              </div>
            </div>
          </div>
          <div className="fixed bottom-6 right-6 z-50 hidden sm:block">
            <ThemeTogglerTwo />
          </div>
        </div>
      </ThemeProvider>
    </div>
  );
}
