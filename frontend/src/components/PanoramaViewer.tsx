import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";

export interface PanoramaViewerHandle {
  getYaw(): number;
}

const PanoramaViewer = forwardRef<
  PanoramaViewerHandle,
  {
    imageUrl: string;
    heading: number | null;
    initialYaw: number;
    onYawChange: (yaw: number) => void;
  }
>(function PanoramaViewer({
  imageUrl,
  heading,
  initialYaw,
  onYawChange,
}, ref) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<PannellumViewer | null>(null);
  const [error, setError] = useState("");
  useImperativeHandle(ref, () => ({
    getYaw: () => viewerRef.current?.getYaw() ?? 0,
  }));

  useEffect(() => {
    if (!containerRef.current) return;

    let disposed = false;
    let yawTimer: number | undefined;
    let viewer: PannellumViewer | undefined;

    const initialize = async () => {
      try {
        await Promise.all([
          import("pannellum/build/pannellum.css"),
          import("pannellum"),
        ]);
        if (disposed || !containerRef.current) return;

        viewer = window.pannellum.viewer(containerRef.current, {
          type: "equirectangular",
          panorama: imageUrl,
          autoLoad: true,
          showControls: true,
          compass: heading !== null,
          northOffset: heading ?? 0,
          yaw: initialYaw,
          hfov: 100,
          showZoomCtrl: true,
          keyboardZoom: true,
          mouseZoom: true,
          draggable: true,
          friction: 0.15,
        });
        viewerRef.current = viewer;
        viewer.on("load", () => setError(""));
        viewer.on("error", () =>
          setError("Không thể tải ảnh 360°. Vui lòng thử lại."),
        );
        if (heading !== null) {
          yawTimer = window.setInterval(() => {
            if (viewer) onYawChange(viewer.getYaw());
          }, 500);
        }
      } catch {
        if (!disposed) {
          setError("Không thể khởi tạo trình xem ảnh 360°.");
        }
      }
    };

    setError("");
    void initialize();
    return () => {
      disposed = true;
      if (yawTimer !== undefined) window.clearInterval(yawTimer);
      viewer?.destroy();
      viewerRef.current = null;
    };
  }, [heading, imageUrl, initialYaw, onYawChange]);

  return (
    <>
      <div
        ref={containerRef}
        className="panorama-canvas"
        aria-label="Ảnh toàn cảnh 360 độ"
      />
      {error && (
        <div className="viewer-alert" role="alert">{error}</div>
      )}
    </>
  );
});

export default PanoramaViewer;
