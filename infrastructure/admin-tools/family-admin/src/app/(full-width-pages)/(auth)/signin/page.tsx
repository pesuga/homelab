import SignInFormIntegrated from "@/components/auth/SignInFormIntegrated";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign In | Family Assistant Admin",
  description: "Sign in to Family Assistant Admin Panel",
};

export default function SignIn() {
  return <SignInFormIntegrated />;
}
