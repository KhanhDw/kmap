import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../api/client";

export default function Home() {
  const { data, isError, isLoading } = useQuery({
    queryKey: ["health"],
    queryFn: () => apiGet<{ status: string }>("/health"),
  });

  const statusText = isLoading
    ? "đang kiểm tra..."
    : isError
      ? "API lỗi"
      : `API: ${data?.status}`;

  const statusClass = isError
    ? "bg-red-100 text-red-700"
    : isLoading
      ? "bg-slate-100 text-slate-700"
      : "bg-green-100 text-green-700";

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-6">
      <h1 className="text-3xl font-bold">KMap</h1>
      <p className="text-slate-600">Bản đồ 360° Tân Châu · Phú Tân · An Giang</p>
      <div className={`rounded px-4 py-2 ${statusClass}`}>{statusText}</div>
      <a href="/admin" className="text-sm text-blue-600 underline">
        Vào trang admin (placeholder)
      </a>
    </main>
  );
}
