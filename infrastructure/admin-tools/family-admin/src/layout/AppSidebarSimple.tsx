"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSidebar } from "@/context/SidebarContext";
import { menuGroups } from "@/config/sidebarMenu";
import SidebarWidget from "./SidebarWidget";

const AppSidebarSimple: React.FC = () => {
  const pathname = usePathname();
  const { isExpanded, isHovered, isMobileOpen, toggleMobileSidebar } = useSidebar();

  const sidebarClass = isMobileOpen
    ? "translate-x-0"
    : isExpanded || isHovered
    ? "lg:w-[290px]"
    : "lg:w-[90px]";

  return (
    <>
      <aside
        className={`fixed left-0 top-0 z-999999 flex h-screen w-[290px] flex-col overflow-y-hidden bg-white transition-all duration-300 ease-in-out dark:bg-gray-900 lg:static lg:translate-x-0 ${sidebarClass} ${
          isMobileOpen ? "" : "max-lg:-translate-x-full"
        }`}
      >
        {/* Sidebar Header */}
        <div className="flex items-center justify-between gap-2 px-6 py-5 lg:py-6">
          <Link href="/">
            <div className="flex items-center gap-2">
              <svg
                className="fill-current text-blue-600"
                width="32"
                height="32"
                viewBox="0 0 32 32"
                fill="none"
              >
                <path d="M16 4C12.8 4 10 5.6 8.4 8.4C6.8 6.8 4.4 6 2 6V8C4 8 6 8.8 7.2 10.4C6.4 12.4 6 14.4 6 16.4C6 23.2 11.2 28.4 18 28.4C24.8 28.4 30 23.2 30 16.4C30 9.6 24.8 4.4 18 4.4H16V4ZM16 6.4H18C23.6 6.4 28 10.8 28 16.4C28 22 23.6 26.4 18 26.4C12.4 26.4 8 22 8 16.4C8 14.8 8.4 13.2 9.2 11.6C10.8 13.6 13.2 14.8 16 14.8V12.8C13.6 12.8 11.6 11.6 10.4 9.6C12 7.6 14 6.4 16 6.4Z" />
              </svg>
              {(isExpanded || isHovered || isMobileOpen) && (
                <span className="text-lg font-semibold text-gray-900 dark:text-white">
                  Family Assistant
                </span>
              )}
            </div>
          </Link>
        </div>

        {/* Sidebar Menu */}
        <div className="no-scrollbar flex flex-col overflow-y-auto duration-300 ease-linear">
          <nav className="px-4 py-4 lg:px-6">
            {menuGroups.map((group, groupIndex) => (
              <div key={groupIndex}>
                {(isExpanded || isHovered || isMobileOpen) && (
                  <h3 className="mb-4 ml-4 text-xs font-semibold text-gray-500 dark:text-gray-400">
                    {group.name}
                  </h3>
                )}

                <ul className="mb-6 flex flex-col gap-1.5">
                  {group.menuItems.map((menuItem, menuIndex) => {
                    const isActive = pathname === menuItem.route;

                    return (
                      <li key={menuIndex}>
                        <Link
                          href={menuItem.route}
                          onClick={() => isMobileOpen && toggleMobileSidebar()}
                          className={`group relative flex items-center gap-3 rounded-lg px-4 py-3 font-medium duration-300 ease-in-out ${
                            isActive
                              ? "bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400"
                              : "text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
                          }`}
                        >
                          <span className={`${isActive ? "text-blue-600 dark:text-blue-400" : ""}`}>
                            {menuItem.icon}
                          </span>
                          {(isExpanded || isHovered || isMobileOpen) && (
                            <span>{menuItem.label}</span>
                          )}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </nav>
        </div>

        {/* Sidebar Widget */}
        {(isExpanded || isHovered || isMobileOpen) && <SidebarWidget />}
      </aside>
    </>
  );
};

export default AppSidebarSimple;
