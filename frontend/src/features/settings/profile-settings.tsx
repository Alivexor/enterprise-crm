"use client";

import { T } from "@/components/i18n/i18n-provider";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { SettingsNavigation } from "@/features/settings/settings-navigation";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/services/api-client";
import { userManagementService } from "@/services/user-management-service";

const inputClassName =
  "w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to save your profile.";
}

export function ProfileSettings() {
  const { refreshUser, user } = useAuth();
  const [firstName, setFirstName] = useState(user?.first_name ?? "");
  const [lastName, setLastName] = useState(user?.last_name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isSavingPassword, setIsSavingPassword] = useState(false);
  const [profileMessage, setProfileMessage] = useState<string | null>(null);
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);

  async function updateProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSavingProfile(true);
    setProfileMessage(null);
    try {
      await userManagementService.updateProfile({
        email: email.trim(),
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      });
      await refreshUser();
      setProfileMessage("Profile updated successfully.");
    } catch (caughtError) {
      setProfileMessage(getErrorMessage(caughtError));
    } finally {
      setIsSavingProfile(false);
    }
  }

  async function updatePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordMessage(null);
    if (newPassword !== confirmPassword) {
      setPasswordMessage("The new password confirmation does not match.");
      return;
    }

    setIsSavingPassword(true);
    try {
      await userManagementService.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordMessage("Password changed successfully.");
    } catch (caughtError) {
      setPasswordMessage(getErrorMessage(caughtError));
    } finally {
      setIsSavingPassword(false);
    }
  }

  return (
    <section className="crm-page mx-auto max-w-4xl">
      <p className="crm-kicker"><T>Settings</T></p>
      <h1 className="crm-title mt-3"><T>Profile</T></h1>
      <p className="crm-subtitle mt-3"><T>Update the personal information used throughout the CRM.</T></p>
      <div className="mt-6"><SettingsNavigation compact /></div>

      <form className="crm-card mt-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6" onSubmit={(event) => void updateProfile(event)}>
        <h2 className="text-lg font-semibold text-slate-950 dark:text-white"><T>Personal information</T></h2>
        <div className="mt-6 grid gap-5 sm:grid-cols-2">
          <div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="profile-first-name"><T>First name</T></label><input className={inputClassName} id="profile-first-name" maxLength={100} minLength={1} onChange={(event) => setFirstName(event.target.value)} required value={firstName} /></div>
          <div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="profile-last-name"><T>Last name</T></label><input className={inputClassName} id="profile-last-name" maxLength={100} minLength={1} onChange={(event) => setLastName(event.target.value)} required value={lastName} /></div>
          <div className="space-y-2 sm:col-span-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="profile-email"><T>Email address</T></label><input className={inputClassName} id="profile-email" maxLength={255} onChange={(event) => setEmail(event.target.value)} required type="email" value={email} /></div>
        </div>
        <div className="mt-6 flex items-center justify-between gap-4"><p className="text-sm text-slate-500" role="status">{profileMessage}</p><Button disabled={isSavingProfile} type="submit">{isSavingProfile ? <T>Saving...</T> : <T>Save profile</T>}</Button></div>
      </form>

      <form className="mt-6 crm-card rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6" onSubmit={(event) => void updatePassword(event)}>
        <h2 className="text-lg font-semibold text-slate-950 dark:text-white"><T>Change password</T></h2>
        <p className="mt-1 text-sm text-slate-500"><T>Use at least 12 characters and keep this password unique.</T></p>
        <div className="mt-6 grid gap-5 sm:grid-cols-2">
          <div className="space-y-2 sm:col-span-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="current-password"><T>Current password</T></label><input autoComplete="current-password" className={inputClassName} id="current-password" onChange={(event) => setCurrentPassword(event.target.value)} required type="password" value={currentPassword} /></div>
          <div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="new-password"><T>New password</T></label><input autoComplete="new-password" className={inputClassName} id="new-password" minLength={12} onChange={(event) => setNewPassword(event.target.value)} required type="password" value={newPassword} /></div>
          <div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="confirm-password"><T>Confirm new password</T></label><input autoComplete="new-password" className={inputClassName} id="confirm-password" minLength={12} onChange={(event) => setConfirmPassword(event.target.value)} required type="password" value={confirmPassword} /></div>
        </div>
        <div className="mt-6 flex items-center justify-between gap-4"><p className="text-sm text-slate-500" role="status">{passwordMessage}</p><Button disabled={isSavingPassword} type="submit">{isSavingPassword ? <T>Saving...</T> : <T>Change password</T>}</Button></div>
      </form>
    </section>
  );
}
