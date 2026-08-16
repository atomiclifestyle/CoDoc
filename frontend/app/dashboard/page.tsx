"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSessionUser } from "@/lib/useSession";
import DashboardClient from "@/components/DashboardClient";
import FullPageLoader from "@/components/FullPageLoader";

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading } = useSessionUser();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/");
    }
  }, [loading, user, router]);

  if (loading || !user) {
    return <FullPageLoader />;
  }

  return (
    <DashboardClient
      userName={user.first_name}
      userEmail={user.email}
      isDemo={!!user.is_demo}
    />
  );
}
