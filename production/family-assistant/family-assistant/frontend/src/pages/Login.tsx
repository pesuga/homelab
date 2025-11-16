/**
 * Login Page
 *
 * Dedicated login page for the Family Assistant application.
 * Features a clean, accessible login form with proper error handling.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { LoginForm } from '../components/LoginForm';
import { ThemeToggle } from '../components/ThemeToggle';

export function Login() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
      {/* Left side - Login Form */}
      <div className="flex-1 flex flex-col justify-center py-12 px-4 sm:px-6 lg:flex-none lg:px-8 xl:px-12">
        <div className="mx-auto w-full max-w-sm lg:w-96">
          {/* Logo/Header */}
          <div className="text-center mb-8">
            <div className="flex justify-center items-center mb-6">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2h2a2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2.5 2.5 0 012.5 2.5v1.064M15 20.488V18a2 2 0 01-2 2h-2a2 2 0 01-2-2v-1a2 2 0 00-2-2v-.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <span className="ml-2 text-2xl font-bold text-gray-900 dark:text-white">
                Family Assistant
              </span>
            </div>
            <p className="text-gray-600 dark:text-gray-400">
              Welcome back! Please sign in to your account.
            </p>
          </div>

          {/* Theme Toggle */}
          <div className="flex justify-end mb-6">
            <ThemeToggle />
          </div>

          {/* Login Form */}
          <LoginForm />
        </div>
      </div>

      {/* Right side - Hero/Image */}
      <div className="hidden lg:block lg:w-0 lg:1/2">
        <div className="h-full w-full bg-gradient-to-br from-blue-600 to-purple-700 flex items-center justify-center">
          <div className="max-w-lg mx-auto text-center p-12">
            <div className="text-white">
              <h2 className="text-4xl font-bold mb-4">
                Your Family's AI Assistant
              </h2>
              <p className="text-xl mb-8 opacity-90">
                Secure, private, and tailored for your family's needs
              </p>

              {/* Features */}
              <div className="grid grid-cols-1 gap-6 text-left">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <svg className="w-6 h-6 text-blue-200 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold mb-1">Secure & Private</h3>
                    <p className="text-sm opacity-75">
                      Your family data stays private and secure
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <svg className="w-6 h-6 text-blue-200 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332-.523 4.5-1.747V6.253z"
                      />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold mb-1">Smart & Helpful</h3>
                    <p className="text-sm opacity-75">
                      AI-powered assistance tailored for families
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <svg className="w-6 h-6 text-blue-200 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0H15a4.996 4.996 0 011.928-2.643M7 16a4.996 4.996 0 01-1.928-2.643M3 4a5 5 0 015-2.643 5.924M17 4a5 5 0 001.928-2.643M7 16v-2m0-4V6M7 4v2m0 4v2m0 4v2"
                      />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold mb-1">Family-Friendly</h3>
                    <p className="text-sm opacity-75">
                      Designed with parents and children in mind
                    </p>
                  </div>
                </div>
              </div>

              {/* Stats */}
              <div className="mt-12 grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-3xl font-bold">100%</div>
                  <div className="text-sm opacity-75">Private</div>
                </div>
                <div>
                  <div className="text-3xl font-bold">24/7</div>
                  <div className="text-sm opacity-75">Available</div>
                </div>
                <div>
                  <div className="text-3xl font-bold">5★</div>
                  <div className="text-sm opacity-75">Security</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}