// src/api.ts
import { apiFetch } from "@/lib/apiClient";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

export async function uploadPDF(file: File, accessToken: string) {
  const formData = new FormData();
  formData.append("pdf", file);

  const res = await apiFetch(API_BASE, "/upload", accessToken, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) throw new Error("Failed to upload PDF");
  return res.json();
}

export async function askQuestion(query: string, accessToken: string) {
  const res = await apiFetch(API_BASE, "/ask", accessToken, {
    method: "POST",
    body: JSON.stringify({ query }),
  });

  if (!res.ok) throw new Error("Failed to get response");
  return res.json();
}
