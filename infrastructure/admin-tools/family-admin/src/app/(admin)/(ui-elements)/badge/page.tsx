import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Badge from "@/components/ui/badge/Badge";
import { PlusIcon } from "@/icons";
import { Metadata } from "next";
import React from "react";

export const metadata: Metadata = {
  title: "Next.js Badge | TailAdmin - Next.js Dashboard Template",
  description:
    "This is Next.js Badge page for TailAdmin - Next.js Tailwind CSS Admin Dashboard Template",
  // other metadata
};

export default function BadgePage() {
  return (
    <div>
      <PageBreadcrumb pageTitle="Badges" />
      <div className="space-y-5 sm:space-y-6">
        <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
          <div className="px-6 py-5">
            <h3 className="text-base font-medium text-gray-800 dark:text-white/90">
              With Light Background
            </h3>
          </div>
          <div className="p-6 border-t border-gray-100 dark:border-gray-800 xl:p-10">
            <div className="flex flex-wrap gap-4 sm:items-center sm:justify-center">
              {/* Default Variant */}
              <Badge variant="default">
                Primary
              </Badge>
              <Badge variant="success">
                Success
              </Badge>{" "}
              <Badge variant="destructive">
                Error
              </Badge>{" "}
              <Badge variant="warning">
                Warning
              </Badge>{" "}
              <Badge variant="info">
                Info
              </Badge>
              <Badge variant="secondary">
                Light
              </Badge>
              <Badge variant="outline">
                Dark
              </Badge>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
          <div className="px-6 py-5">
            <h3 className="text-base font-medium text-gray-800 dark:text-white/90">
              With Solid Background
            </h3>
          </div>
          <div className="p-6 border-t border-gray-100 dark:border-gray-800 xl:p-10">
            <div className="flex flex-wrap gap-4 sm:items-center sm:justify-center">
              {/* Solid Variant - using default variant for stronger colors */}
              <Badge variant="default" >
                Primary
              </Badge>
              <Badge variant="success" >
                Success
              </Badge>{" "}
              <Badge variant="destructive" >
                Error
              </Badge>{" "}
              <Badge variant="warning" >
                Warning
              </Badge>{" "}
              <Badge variant="info" >
                Info
              </Badge>
              <Badge variant="secondary" >
                Light
              </Badge>
              <Badge variant="outline" >
                Dark
              </Badge>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
          <div className="px-6 py-5">
            <h3 className="text-base font-medium text-gray-800 dark:text-white/90">
              Light Background with Left Icon
            </h3>
          </div>
          <div className="p-6 border-t border-gray-100 dark:border-gray-800 xl:p-10">
            <div className="flex flex-wrap gap-4 sm:items-center sm:justify-center">
              <Badge variant="default" startIcon={<PlusIcon />}>
                Primary
              </Badge>
              <Badge variant="success" startIcon={<PlusIcon />}>
                Success
              </Badge>{" "}
              <Badge variant="destructive" startIcon={<PlusIcon />}>
                Error
              </Badge>{" "}
              <Badge variant="warning" startIcon={<PlusIcon />}>
                Warning
              </Badge>{" "}
              <Badge variant="info" startIcon={<PlusIcon />}>
                Info
              </Badge>
              <Badge variant="secondary" startIcon={<PlusIcon />}>
                Light
              </Badge>
              <Badge variant="outline" startIcon={<PlusIcon />}>
                Dark
              </Badge>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
          <div className="px-6 py-5">
            <h3 className="text-base font-medium text-gray-800 dark:text-white/90">
              Solid Background with Left Icon
            </h3>
          </div>
          <div className="p-6 border-t border-gray-100 dark:border-gray-800 xl:p-10">
            <div className="flex flex-wrap gap-4 sm:items-center sm:justify-center">
              <Badge variant="default"  startIcon={<PlusIcon />}>
                Primary
              </Badge>
              <Badge variant="success"  startIcon={<PlusIcon />}>
                Success
              </Badge>{" "}
              <Badge variant="destructive"  startIcon={<PlusIcon />}>
                Error
              </Badge>{" "}
              <Badge variant="warning"  startIcon={<PlusIcon />}>
                Warning
              </Badge>{" "}
              <Badge variant="info"  startIcon={<PlusIcon />}>
                Info
              </Badge>
              <Badge variant="secondary"  startIcon={<PlusIcon />}>
                Light
              </Badge>
              <Badge variant="outline"  startIcon={<PlusIcon />}>
                Dark
              </Badge>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
          <div className="px-6 py-5">
            <h3 className="text-base font-medium text-gray-800 dark:text-white/90">
              Light Background with Right Icon
            </h3>
          </div>
          <div className="p-6 border-t border-gray-100 dark:border-gray-800 xl:p-10">
            <div className="flex flex-wrap gap-4 sm:items-center sm:justify-center">
              <Badge variant="default" endIcon={<PlusIcon />}>
                Primary
              </Badge>
              <Badge variant="success" endIcon={<PlusIcon />}>
                Success
              </Badge>{" "}
              <Badge variant="destructive" endIcon={<PlusIcon />}>
                Error
              </Badge>{" "}
              <Badge variant="warning" endIcon={<PlusIcon />}>
                Warning
              </Badge>{" "}
              <Badge variant="info" endIcon={<PlusIcon />}>
                Info
              </Badge>
              <Badge variant="secondary" endIcon={<PlusIcon />}>
                Light
              </Badge>
              <Badge variant="outline" endIcon={<PlusIcon />}>
                Dark
              </Badge>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
          <div className="px-6 py-5">
            <h3 className="text-base font-medium text-gray-800 dark:text-white/90">
              Solid Background with Right Icon
            </h3>
          </div>
          <div className="p-6 border-t border-gray-100 dark:border-gray-800 xl:p-10">
            <div className="flex flex-wrap gap-4 sm:items-center sm:justify-center">
              <Badge variant="default"  endIcon={<PlusIcon />}>
                Primary
              </Badge>
              <Badge variant="success"  endIcon={<PlusIcon />}>
                Success
              </Badge>{" "}
              <Badge variant="destructive"  endIcon={<PlusIcon />}>
                Error
              </Badge>{" "}
              <Badge variant="warning"  endIcon={<PlusIcon />}>
                Warning
              </Badge>{" "}
              <Badge variant="info"  endIcon={<PlusIcon />}>
                Info
              </Badge>
              <Badge variant="secondary"  endIcon={<PlusIcon />}>
                Light
              </Badge>
              <Badge variant="outline"  endIcon={<PlusIcon />}>
                Dark
              </Badge>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
