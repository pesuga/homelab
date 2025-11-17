"use client";

import React from 'react';
import { ThemeProvider } from '@/contexts/theme-context';

interface ClientThemeProviderProps {
  children: React.ReactNode;
}

export default function ClientThemeProvider({ children }: ClientThemeProviderProps) {
  return <ThemeProvider>{children}</ThemeProvider>;
}