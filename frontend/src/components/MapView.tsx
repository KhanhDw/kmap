import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import type { Feature, Geometry, Point } from "geojson";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import "leaflet.markercluster";
import { apiGet } from "../api/client";

export interface PublicMapConfig {
  areas: Array<{
    slug: string;
    name: string;
    bbox: [number, number, number, number];
  }>;
  center: { lat: number; lng: number };
  zoom: number;
  terms_version: string;
  satellite: { url: string; attribution: string; max_zoom: number } | null;
}

interface GeoJSONCollection<P> {
  type: "FeatureCollection";
  features: Array<Feature<Geometry, P>>;
  truncated: boolean;
}

interface RoadProperties {
  id: string;
  source: "osm" | "community";
  highway: string | null;
  road_type: string | null;
  name: string | null;
}

interface PhotoProperties {
  id: string;
  thumbnail_url: string | null;
  heading: number | null;
}

type PhotoCollection = {
  type: "FeatureCollection";
  features: Array<Feature<Point, PhotoProperties>>;
  truncated: boolean;
};

function initialMapState(config: PublicMapConfig) {
  const params = new URLSearchParams(window.location.search);
  const lat = Number(params.get("lat"));
  const lng = Number(params.get("lng"));
  const zoom = Number(params.get("z"));
  const hasLat = params.has("lat") && Number.isFinite(lat) && lat >= -90 && lat <= 90;
  const hasLng = params.has("lng") && Number.isFinite(lng) && lng >= -180 && lng <= 180;
  const hasZoom = params.has("z") && Number.isFinite(zoom) && zoom >= 0 && zoom <= 24;
  return {
    hasViewOverride: hasLat || hasLng || hasZoom,
    center: {
      lat: hasLat ? lat : config.center.lat,
      lng: hasLng ? lng : config.center.lng,
    },
    zoom: hasZoom ? zoom : config.zoom,
    selectedPhoto: params.get("photo"),
  };
}

function updateUrl(map: L.Map, photoId?: string): void {
  const center = map.getCenter();
  const params = new URLSearchParams(window.location.search);
  params.set("lat", center.lat.toFixed(6));
  params.set("lng", center.lng.toFixed(6));
  params.set("z", String(map.getZoom()));
  if (photoId) {
    params.set("photo", photoId);
  }
  const query = params.toString();
  window.history.replaceState(
    window.history.state,
    "",
    `${window.location.pathname}${query ? `?${query}` : ""}`,
  );
}

function popupContent(feature: Feature<Point, PhotoProperties>): HTMLElement {
  const content = document.createElement("div");
  content.className = "photo-popup";
  if (feature.properties.thumbnail_url) {
    const image = document.createElement("img");
    image.src = feature.properties.thumbnail_url;
    image.alt = "Ảnh 360°";
    image.loading = "lazy";
    content.append(image);
  }
  const label = document.createElement("span");
  label.textContent = "Ảnh 360°";
  content.append(label);
  return content;
}

export default function MapView({ config }: { config: PublicMapConfig }) {
  const mapElement = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<L.Map | null>(null);
  const [message, setMessage] = useState("");
  const [showZoomHint, setShowZoomHint] = useState(false);

  useEffect(() => {
    if (!mapElement.current) return;

    const initialState = initialMapState(config);
    const serviceBounds = config.areas.reduce(
      (current, area) => ({
        west: Math.min(current.west, area.bbox[0]),
        south: Math.min(current.south, area.bbox[1]),
        east: Math.max(current.east, area.bbox[2]),
        north: Math.max(current.north, area.bbox[3]),
      }),
      {
        west: Infinity,
        south: Infinity,
        east: -Infinity,
        north: -Infinity,
      },
    );
    const marginLongitude = (serviceBounds.east - serviceBounds.west) * 0.1;
    const marginLatitude = (serviceBounds.north - serviceBounds.south) * 0.1;
    const allowedBounds = {
      west: serviceBounds.west - marginLongitude,
      south: serviceBounds.south - marginLatitude,
      east: serviceBounds.east + marginLongitude,
      north: serviceBounds.north + marginLatitude,
    };
    const map = L.map(mapElement.current, { zoomControl: true });
    if (initialState.hasViewOverride) {
      map.setView(
        [initialState.center.lat, initialState.center.lng],
        initialState.zoom,
      );
    } else {
      const viewportZoom = Math.min(
        config.zoom,
        config.zoom + Math.round(Math.log2(map.getSize().x / 800)),
      );
      map.fitBounds(
        [
          [serviceBounds.south, serviceBounds.west],
          [serviceBounds.north, serviceBounds.east],
        ],
        { maxZoom: viewportZoom, padding: [24, 24] },
      );
    }
    mapInstance.current = map;
    const streetUrl = import.meta.env.VITE_TILE_URL;
    const streetAttribution =
      import.meta.env.VITE_TILE_ATTRIBUTION || "© OpenStreetMap contributors";
    const streetLayer = streetUrl
      ? L.tileLayer(streetUrl, {
          attribution: streetAttribution,
          keepBuffer: 0,
          updateWhenIdle: true,
        })
      : L.layerGroup();
    streetLayer.addTo(map);

    const baseLayers: Record<string, L.Layer> = { "Đường phố (OSM)": streetLayer };
    if (config.satellite) {
      baseLayers["Vệ tinh"] = L.tileLayer(config.satellite.url, {
        attribution: config.satellite.attribution,
        maxZoom: config.satellite.max_zoom,
      });
    }

    const osmRoads = L.layerGroup().addTo(map);
    const communityRoads = L.layerGroup().addTo(map);
    const photoMarkers = L.markerClusterGroup({
      showCoverageOnHover: false,
      iconCreateFunction: (cluster) =>
        L.divIcon({
          className: "photo-cluster",
          html: `<span>${cluster.getChildCount()}</span>`,
          iconSize: [36, 36],
        }),
    }).addTo(map);
    L.control
      .layers(
        baseLayers,
        {
          "Đường OSM": osmRoads,
          "Đường cộng đồng": communityRoads,
          "Ảnh 360°": photoMarkers,
        },
        { collapsed: true },
      )
      .addTo(map);

    const abortControllers = new Set<AbortController>();
    let debounceTimer: number | undefined;
    let initialPhotoHandled = false;
    const updateViewport = () => {
      if (debounceTimer !== undefined) window.clearTimeout(debounceTimer);
      debounceTimer = window.setTimeout(async () => {
        updateUrl(map);
        const bounds = map.getBounds();
        const minLongitude = Math.max(bounds.getWest(), allowedBounds.west);
        const minLatitude = Math.max(bounds.getSouth(), allowedBounds.south);
        const maxLongitude = Math.min(bounds.getEast(), allowedBounds.east);
        const maxLatitude = Math.min(bounds.getNorth(), allowedBounds.north);
        if (minLongitude >= maxLongitude || minLatitude >= maxLatitude) {
          osmRoads.clearLayers();
          communityRoads.clearLayers();
          photoMarkers.clearLayers();
          setShowZoomHint(false);
          setMessage("");
          return;
        }
        const bbox = [
          minLongitude,
          minLatitude,
          maxLongitude,
          maxLatitude,
        ]
          .map((coordinate) => coordinate.toFixed(6))
          .join(",");
        const zoom = Math.round(map.getZoom());
        const controller = new AbortController();
        abortControllers.add(controller);
        for (const active of abortControllers) {
          if (active !== controller) active.abort();
        }
        try {
          const [roads, photos] = await Promise.all([
            apiGet<GeoJSONCollection<RoadProperties>>(
              `/roads?bbox=${encodeURIComponent(bbox)}&layer=all&zoom=${zoom}`,
              controller.signal,
            ),
            apiGet<PhotoCollection>(
              `/photos?bbox=${encodeURIComponent(bbox)}`,
              controller.signal,
            ),
          ]);
          if (controller.signal.aborted) return;
          osmRoads.clearLayers();
          communityRoads.clearLayers();
          const osmFeatures = roads.features.filter(
            (feature) => feature.properties?.source === "osm",
          );
          const communityFeatures = roads.features.filter(
            (feature) => feature.properties?.source === "community",
          );
          L.geoJSON(osmFeatures, {
            style: { color: "#2563eb", weight: 3, opacity: 0.8 },
            onEachFeature: (feature, layer) => {
              if (feature.properties?.name) layer.bindTooltip(feature.properties.name);
            },
          }).addTo(osmRoads);
          L.geoJSON(communityFeatures, {
            style: { color: "#16a34a", weight: 3, opacity: 0.9, dashArray: "6 4" },
            onEachFeature: (feature, layer) => {
              if (feature.properties?.name) layer.bindTooltip(feature.properties.name);
            },
          }).addTo(communityRoads);

          photoMarkers.clearLayers();
          for (const feature of photos.features) {
            const [longitude, latitude] = feature.geometry.coordinates;
            const marker = L.circleMarker([latitude, longitude], {
              radius: 7,
              color: "#fff",
              weight: 2,
              fillColor: "#e11d48",
              fillOpacity: 1,
            }).bindPopup(popupContent(feature));
            marker.on("click", () => updateUrl(map, feature.properties.id));
            photoMarkers.addLayer(marker);
            if (
              !initialPhotoHandled &&
              initialState.selectedPhoto === feature.properties.id
            ) {
              marker.openPopup();
              initialPhotoHandled = true;
            }
          }
          setShowZoomHint(photos.truncated && zoom < 14);
          setMessage("");
        } catch (error) {
          if (!controller.signal.aborted) {
            setMessage(
              error instanceof Error
                ? `Không thể tải dữ liệu bản đồ: ${error.message}`
                : "Không thể tải dữ liệu bản đồ.",
            );
          }
        } finally {
          abortControllers.delete(controller);
        }
      }, 250);
    };
    map.on("moveend", updateViewport);
    updateViewport();

    return () => {
      if (debounceTimer !== undefined) window.clearTimeout(debounceTimer);
      map.off("moveend", updateViewport);
      for (const controller of abortControllers) controller.abort();
      map.remove();
      mapInstance.current = null;
    };
  }, [config]);

  const locate = () => {
    if (!navigator.geolocation) {
      setMessage("Trình duyệt không hỗ trợ định vị.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const map = mapInstance.current;
        if (map) {
          map.flyTo([position.coords.latitude, position.coords.longitude], 16);
        }
        setMessage("");
      },
      (error) => {
        const messageByCode: Record<number, string> = {
          1: "Bạn chưa cho phép truy cập vị trí.",
          2: "Không xác định được vị trí hiện tại.",
          3: "Yêu cầu định vị đã hết thời gian chờ.",
        };
        setMessage(messageByCode[error.code] ?? "Không thể lấy vị trí hiện tại.");
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  };

  return (
    <main className="map-screen">
      <div ref={mapElement} className="map-canvas" aria-label="Bản đồ KMap" />
      <div className="map-brand" aria-label="KMap">
        <strong>KMap</strong>
        <span>Tân Châu · Phú Tân · An Giang</span>
      </div>
      <button className="gps-button" type="button" onClick={locate}>
        Vị trí của tôi
      </button>
      {showZoomHint && (
        <div className="map-hint" role="status">
          Phóng to bản đồ để xem đầy đủ ảnh.
        </div>
      )}
      {message && (
        <div className="map-message" role="alert">
          {message}
        </div>
      )}
    </main>
  );
}
