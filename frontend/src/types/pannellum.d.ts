interface PannellumViewer {
  destroy(): void;
  getYaw(): number;
  getPitch(): number;
  getHfov(): number;
  setYaw(yaw: number, duration?: number): void;
  on(event: string, callback: () => void): PannellumViewer;
  off(event: string, callback: () => void): PannellumViewer;
}

interface Pannellum {
  viewer(
    container: HTMLElement,
    config: {
      type: "equirectangular";
      panorama: string;
      autoLoad: true;
      showControls: true;
      compass: boolean;
      northOffset: number;
      yaw: number;
      hfov: number;
      showZoomCtrl: true;
      keyboardZoom: true;
      mouseZoom: true;
      draggable: true;
      friction: number;
    },
  ): PannellumViewer;
}

interface Window {
  pannellum: Pannellum;
}

declare module "pannellum";
