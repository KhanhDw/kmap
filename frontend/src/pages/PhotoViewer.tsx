import { useCallback, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, X } from "lucide-react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import {
  getPhotoNeighbors,
  getPublicPhoto,
  type PhotoNeighbor,
  type PublicPhoto,
} from "../api/photos";
import PanoramaViewer, {
  type PanoramaViewerHandle,
} from "../components/PanoramaViewer";
import {
  getMaxTextureSize,
  pickVariant,
} from "../lib/photoVariant";

interface ViewerNavigationState {
  compassBearing?: number;
}

function normalizeBearing(bearing: number): number {
  return ((bearing % 360) + 360) % 360;
}

function toViewerYaw(bearing: number, northOffset: number): number {
  const yaw = normalizeBearing(bearing - northOffset);
  return yaw > 180 ? yaw - 360 : yaw;
}

function isMobileLike(): boolean {
  return (
    navigator.maxTouchPoints > 0 ||
    window.matchMedia("(max-width: 767px)").matches
  );
}

function formatCapturedAt(capturedAt: string | null): string | null {
  if (!capturedAt) return null;
  const date = new Date(capturedAt);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium" }).format(date);
}

function photoSearch(search: string, photoId: string): string {
  const params = new URLSearchParams(search);
  params.set("photo", photoId);
  return `?${params.toString()}`;
}

function PhotoLink({
  photo,
  label,
  compassBearing,
  onNavigate,
}: {
  photo: PhotoNeighbor;
  label: string;
  compassBearing: number;
  onNavigate: (photoId: string, compassBearing: number) => void;
}) {
  return (
    <button
      className="nearby-photo"
      type="button"
      onClick={() => onNavigate(photo.id, compassBearing)}
    >
      {photo.thumbnail_url ? (
        <img src={photo.thumbnail_url} alt="" loading="lazy" />
      ) : (
        <span className="nearby-photo-placeholder" aria-hidden="true" />
      )}
      <span>
        <strong>{label}</strong>
        <small>{photo.distance.toFixed(0)} m</small>
      </span>
    </button>
  );
}

function createCompassBearing(
  viewer: PanoramaViewerHandle | null,
  photo: PublicPhoto,
): number {
  const yaw = viewer?.getYaw() ?? 0;
  return normalizeBearing(yaw + (photo.heading ?? 0));
}

function PhotoViewerContent({ photoId }: { photoId: string }) {
  const viewerRef = useRef<PanoramaViewerHandle | null>(null);
  const location = useLocation();
  const navigate = useNavigate();
  const navigationState = location.state as ViewerNavigationState | null;
  const [bearing, setBearing] = useState<number>();
  const { data: photo, isLoading, error } = useQuery({
    queryKey: ["public-photo", photoId],
    queryFn: () => getPublicPhoto(photoId),
  });
  const variant = useMemo(
    () => pickVariant(getMaxTextureSize(), isMobileLike()),
    [],
  );
  const imageUrl = photo
    ? variant === "mobile"
      ? photo.mobile_url
      : photo.display_url
    : null;
  const photoBearing =
    photo?.heading === null || photo?.heading === undefined
      ? undefined
      : bearing ?? photo.heading;
  const handleYawChange = useCallback(
    (yaw: number) => {
      if (photo?.heading === null || photo?.heading === undefined) return;
      const nextBearing =
        Math.round(normalizeBearing(yaw + photo.heading) / 5) * 5 % 360;
      setBearing((current) =>
        current === nextBearing ? current : nextBearing,
      );
    },
    [photo?.heading],
  );
  const neighborsQuery = useQuery({
    queryKey: ["photo-neighbors", photoId, photoBearing],
    queryFn: () => getPhotoNeighbors(photoId, photoBearing),
    enabled: photo !== undefined,
  });

  const returnToMap = () => {
    navigate({ pathname: "/", search: location.search });
  };

  const navigateToPhoto = (nextPhotoId: string, compassBearing: number) => {
    navigate(
      {
        pathname: `/photo/${encodeURIComponent(nextPhotoId)}`,
        search: photoSearch(location.search, nextPhotoId),
      },
      { state: { compassBearing } satisfies ViewerNavigationState },
    );
  };

  const currentCompassBearing = () =>
    photo ? createCompassBearing(viewerRef.current, photo) : 0;

  if (isLoading) {
    return (
      <main className="viewer-message" role="status">
        Đang tải ảnh 360°...
      </main>
    );
  }
  if (error || !photo) {
    return (
      <main className="viewer-message viewer-error" role="alert">
        <p>{error instanceof Error ? error.message : "Không tìm thấy ảnh công khai."}</p>
        <button type="button" onClick={returnToMap}>Quay lại bản đồ</button>
      </main>
    );
  }
  if (!imageUrl) {
    return (
      <main className="viewer-message viewer-error" role="alert">
        <p>Ảnh này hiện không có tệp hiển thị.</p>
        <button type="button" onClick={returnToMap}>Quay lại bản đồ</button>
      </main>
    );
  }

  const capturedAt = formatCapturedAt(photo.captured_at);
  const neighbors = neighborsQuery.data;
  const selectedPhoto = (candidate: PhotoNeighbor, label: string) => (
    <PhotoLink
      key={`${label}-${candidate.id}`}
      photo={candidate}
      label={label}
      compassBearing={currentCompassBearing()}
      onNavigate={navigateToPhoto}
    />
  );

  return (
    <main className="photo-viewer">
      <PanoramaViewer
        ref={viewerRef}
        imageUrl={imageUrl}
        heading={photo.heading}
        initialYaw={
          navigationState?.compassBearing === undefined
            ? 0
            : toViewerYaw(navigationState.compassBearing, photo.heading ?? 0)
        }
        onYawChange={handleYawChange}
      />
      <header className="viewer-header">
        <button
          className="viewer-close"
          type="button"
          aria-label="Đóng ảnh và quay lại bản đồ"
          onClick={returnToMap}
        >
          <X aria-hidden="true" />
        </button>
        <div className="viewer-photo-info">
          <strong>Ảnh 360°</strong>
          <span>{photo.contributor.display_name}</span>
          {capturedAt && <time dateTime={photo.captured_at ?? undefined}>{capturedAt}</time>}
        </div>
      </header>
      {neighbors && (
        <nav className="viewer-navigation" aria-label="Điều hướng ảnh 360°">
          <button
            className="viewer-navigation-button"
            type="button"
            aria-label="Lùi tới ảnh phía sau"
            disabled={!neighbors.backward}
            onClick={() =>
              neighbors.backward &&
              navigateToPhoto(
                neighbors.backward.id,
                currentCompassBearing(),
              )
            }
          >
            <ArrowDown aria-hidden="true" />
            <span>Lùi</span>
          </button>
          <button
            className="viewer-navigation-button"
            type="button"
            aria-label="Tiến tới ảnh phía trước"
            disabled={!neighbors.forward}
            onClick={() =>
              neighbors.forward &&
              navigateToPhoto(
                neighbors.forward.id,
                currentCompassBearing(),
              )
            }
          >
            <ArrowUp aria-hidden="true" />
            <span>Tiến</span>
          </button>
        </nav>
      )}
      <section className="viewer-neighbors" aria-label="Ảnh lân cận">
        {neighborsQuery.isError && (
          <p className="neighbors-error" role="alert">
            Không thể tải ảnh lân cận.
          </p>
        )}
        {neighbors ? (
          <>
            {neighbors.nearby.length > 0 && (
              <div className="nearby-list">
                <strong>Ảnh gần đây</strong>
                {neighbors.nearby.map((candidate) =>
                  selectedPhoto(candidate, "Ảnh gần"),
                )}
              </div>
            )}
          </>
        ) : (
          !neighborsQuery.isError && <p>Đang tìm ảnh lân cận...</p>
        )}
      </section>
    </main>
  );
}

export default function PhotoViewer() {
  const { photoId } = useParams();
  if (!photoId) {
    return (
      <main className="viewer-message viewer-error" role="alert">
        <p>Không tìm thấy mã ảnh.</p>
        <a href="/">Quay lại bản đồ</a>
      </main>
    );
  }
  return <PhotoViewerContent photoId={photoId} />;
}
