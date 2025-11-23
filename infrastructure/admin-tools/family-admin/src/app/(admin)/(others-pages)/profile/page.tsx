"use client";
import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { UserProfile as ApiUserProfile } from "@/lib/api-client";
import UserAddressCard from "@/components/user-profile/UserAddressCard";
import UserInfoCard from "@/components/user-profile/UserInfoCard";
import UserMetaCard from "@/components/user-profile/UserMetaCard";

// Extended profile interface for UI components
interface UserProfile extends ApiUserProfile {
  bio?: string;
  phone?: string;
  location?: string;
  social_links?: {
    facebook?: string;
    twitter?: string;
    linkedin?: string;
    instagram?: string;
  };
  address?: {
    country?: string;
    city_state?: string;
    postal_code?: string;
    tax_id?: string;
  };
}

export default function Profile() {
  const { user } = useAuth();
  const [isUpdating, setIsUpdating] = useState(false);

  // Mock profile data for demo purposes - in real implementation, this would come from an API
  const mockProfile: UserProfile | null = user ? {
    ...user,
    bio: "Team Manager",
    phone: "+09 363 398 46",
    location: "Arizona, United States",
    social_links: {
      facebook: "https://www.facebook.com/PimjoHQ",
      twitter: "https://x.com/PimjoHQ",
      linkedin: "https://www.linkedin.com/company/pimjo",
      instagram: "https://instagram.com/PimjoHQ"
    },
    address: {
      country: "United States",
      city_state: "Phoenix, Arizona, United States",
      postal_code: "ERT 2489",
      tax_id: "AS4568384"
    }
  } : null;

  const handleProfileUpdate = async (updates: Partial<UserProfile>) => {
    if (!user) return;

    setIsUpdating(true);
    try {
      // Simulate API call - in real implementation, this would call the backend API
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log("Profile updated with:", updates);
      console.log("Profile updated successfully!");
    } catch (error) {
      console.error("Failed to update profile:", error);
      alert("Failed to update profile. Please try again.");
    } finally {
      setIsUpdating(false);
    }
  };

  // Remove loading and error states since we're using mock data

  return (
    <div>
      <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] lg:p-6">
        <h3 className="mb-5 text-lg font-semibold text-gray-800 dark:text-white/90 lg:mb-7">
          Profile
        </h3>
        <div className="space-y-6">
          <UserMetaCard
            profile={mockProfile}
            onUpdate={handleProfileUpdate}
            isLoading={isUpdating}
          />
          <UserInfoCard
            profile={mockProfile}
            onUpdate={handleProfileUpdate}
            isLoading={isUpdating}
          />
          <UserAddressCard
            profile={mockProfile}
            onUpdate={handleProfileUpdate}
            isLoading={isUpdating}
          />
        </div>
      </div>
    </div>
  );
}
