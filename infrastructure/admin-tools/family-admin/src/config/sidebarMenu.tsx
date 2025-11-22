/**
 * Sidebar Menu Configuration for Family Assistant
 */

import React from "react";

export interface MenuItem {
  icon: React.ReactNode;
  label: string;
  route: string;
  children?: MenuItem[];
}

export interface MenuGroup {
  name: string;
  menuItems: MenuItem[];
}

// Home Icon
const HomeIcon = () => (
  <svg className="fill-current" width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M10.7071 2.29289C10.3166 1.90237 9.68342 1.90237 9.29289 2.29289L2.29289 9.29289C1.90237 9.68342 1.90237 10.3166 2.29289 10.7071C2.68342 11.0976 3.31658 11.0976 3.70711 10.7071L4 10.4142V17C4 17.5523 4.44772 18 5 18H7C7.55228 18 8 17.5523 8 17V15C8 14.4477 8.44772 14 9 14H11C11.5523 14 12 14.4477 12 15V17C12 17.5523 12.4477 18 13 18H15C15.5523 18 16 17.5523 16 17V10.4142L16.2929 10.7071C16.6834 11.0976 17.3166 11.0976 17.7071 10.7071C18.0976 10.3166 18.0976 9.68342 17.7071 9.29289L10.7071 2.29289Z" />
  </svg>
);

// Book Icon (Knowledge)
const BookIcon = () => (
  <svg className="fill-current" width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M4 4C4 2.89543 4.89543 2 6 2H14C15.1046 2 16 2.89543 16 4V16C16 17.1046 15.1046 18 14 18H6C4.89543 18 4 17.1046 4 16V4ZM6 4V16H14V4H6Z" />
    <path d="M7 7H13V9H7V7Z" />
    <path d="M7 11H13V13H7V11Z" />
  </svg>
);

// Plug Icon (MCP/Connections)
const PlugIcon = () => (
  <svg className="fill-current" width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M7 2C7 1.44772 7.44772 1 8 1C8.55228 1 9 1.44772 9 2V4H11V2C11 1.44772 11.4477 1 12 1C12.5523 1 13 1.44772 13 2V4H14C15.1046 4 16 4.89543 16 6V8C16 9.10457 15.1046 10 14 10H13V13C13 14.6569 11.6569 16 10 16C8.34315 16 7 14.6569 7 13V10H6C4.89543 10 4 9.10457 4 8V6C4 4.89543 4.89543 4 6 4H7V2ZM9 6H11V13C11 13.5523 10.5523 14 10 14C9.44772 14 9 13.5523 9 13V6ZM6 6V8H14V6H6Z" />
  </svg>
);

// Users Icon (Family)
const UsersIcon = () => (
  <svg className="fill-current" width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M9 6C9 7.65685 7.65685 9 6 9C4.34315 9 3 7.65685 3 6C3 4.34315 4.34315 3 6 3C7.65685 3 9 4.34315 9 6Z" />
    <path d="M17 6C17 7.65685 15.6569 9 14 9C12.3431 9 11 7.65685 11 6C11 4.34315 12.3431 3 14 3C15.6569 3 17 4.34315 17 6Z" />
    <path d="M12.9291 17C12.9758 16.6734 13 16.3395 13 16C13 14.3648 12.4393 12.8606 11.4998 11.6691C12.2352 11.2435 13.0892 11 14 11C16.7614 11 19 13.2386 19 16V17H12.9291Z" />
    <path d="M6 11C8.76142 11 11 13.2386 11 16V17H1V16C1 13.2386 3.23858 11 6 11Z" />
  </svg>
);

// Cog Icon (Settings)
const SettingsIcon = () => (
  <svg className="fill-current" width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path fillRule="evenodd" clipRule="evenodd" d="M11.49 3.17C11.11 1.61 8.89 1.61 8.51 3.17C8.36 3.79 7.73 4.19 7.09 4.05C5.52 3.71 4.21 5.02 4.55 6.59C4.69 7.23 4.29 7.86 3.67 8.01C2.11 8.39 2.11 10.61 3.67 10.99C4.29 11.14 4.69 11.77 4.55 12.41C4.21 13.98 5.52 15.29 7.09 14.95C7.73 14.81 8.36 15.21 8.51 15.83C8.89 17.39 11.11 17.39 11.49 15.83C11.64 15.21 12.27 14.81 12.91 14.95C14.48 15.29 15.79 13.98 15.45 12.41C15.31 11.77 15.71 11.14 16.33 10.99C17.89 10.61 17.89 8.39 16.33 8.01C15.71 7.86 15.31 7.23 15.45 6.59C15.79 5.02 14.48 3.71 12.91 4.05C12.27 4.19 11.64 3.79 11.49 3.17ZM10 13C11.6569 13 13 11.6569 13 10C13 8.34315 11.6569 7 10 7C8.34315 7 7 8.34315 7 10C7 11.6569 8.34315 13 10 13Z" />
  </svg>
);

// Chat Icon
const ChatIcon = () => (
  <svg className="fill-current" width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path fillRule="evenodd" clipRule="evenodd" d="M18 10C18 14.4183 14.4183 18 10 18C8.87472 18 7.80447 17.7563 6.84254 17.3155L3 18L3.68451 14.1575C3.24374 13.1955 3 12.1253 3 11C3 6.58172 6.58172 3 11 3C15.4183 3 19 6.58172 19 11C19 11.3387 18.9793 11.6724 18.9392 12H18C18 11.6724 18 11.3387 18 11C18 7.13401 14.866 4 11 4C7.13401 4 4 7.13401 4 11C4 12.0929 4.26477 13.1175 4.73542 14.0141L4.92923 14.3762L4.5 16.5L6.62378 16.0708L6.98593 16.2646C7.88252 16.7352 8.90714 17 10 17C13.866 17 17 13.866 17 10H18Z" />
    <circle cx="7" cy="10" r="1" />
    <circle cx="10" cy="10" r="1" />
    <circle cx="13" cy="10" r="1" />
  </svg>
);

export const menuGroups: MenuGroup[] = [
  {
    name: "MAIN",
    menuItems: [
      {
        icon: <HomeIcon />,
        label: "Home",
        route: "/",
      },
      {
        icon: <ChatIcon />,
        label: "Chat",
        route: "/chat",
      },
    ],
  },
  {
    name: "FAMILY",
    menuItems: [
      {
        icon: <BookIcon />,
        label: "Shared Knowledge",
        route: "/knowledge",
      },
      {
        icon: <UsersIcon />,
        label: "MyFamily",
        route: "/family",
      },
    ],
  },
  {
    name: "SYSTEM",
    menuItems: [
      {
        icon: <PlugIcon />,
        label: "MCP & Tools",
        route: "/mcp",
      },
      {
        icon: <SettingsIcon />,
        label: "Settings",
        route: "/settings",
      },
    ],
  },
];
