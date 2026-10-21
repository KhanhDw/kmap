import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../api/client";
import MapView, { type PublicMapConfig } from "../components/MapView";

export default function Home() {
  const { data, isError, isLoading } = useQuery({
    queryKey: ["map-config"],
    queryFn: () => apiGet<PublicMapConfig>("/config"),
  });

  if (isLoading) {
    return (
      <main className="grid min-h-screen place-items-center text-slate-700">
        Đang tải bản đồ...
      </main>
    );
  }
  if (isError || !data) {
    return (
      <main className="grid min-h-screen place-items-center p-6 text-center text-red-700">
        Không thể tải cấu hình bản đồ. Vui lòng thử tải lại trang.
      </main>
    );
  }
  return (
    <MapView config={data} />
  );
}
