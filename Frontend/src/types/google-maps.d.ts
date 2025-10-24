declare global {
  interface Window {
    google: typeof google;
  }

  namespace google {
    namespace maps {
      class Map {
        constructor(mapDiv: Element | null, opts?: MapOptions);
        fitBounds(bounds: LatLngBounds): void;
      }

      class Marker {
        constructor(opts?: MarkerOptions);
        setMap(map: Map | null): void;
        addListener(eventName: string, handler: Function): void;
        getPosition(): LatLng | undefined;
      }

      class InfoWindow {
        constructor(opts?: InfoWindowOptions);
        open(map?: Map, anchor?: Marker): void;
      }

      class LatLng {
        constructor(lat: number, lng: number);
      }

      class LatLngBounds {
        constructor();
        extend(point: LatLng): void;
      }

      enum MapTypeId {
        ROADMAP = 'roadmap',
        SATELLITE = 'satellite',
        HYBRID = 'hybrid',
        TERRAIN = 'terrain'
      }

      enum SymbolPath {
        CIRCLE = 0,
        FORWARD_CLOSED_ARROW = 1,
        FORWARD_OPEN_ARROW = 2,
        BACKWARD_CLOSED_ARROW = 3,
        BACKWARD_OPEN_ARROW = 4
      }

      interface MapOptions {
        center?: LatLng | LatLngLiteral;
        zoom?: number;
        mapTypeId?: MapTypeId;
        styles?: MapTypeStyle[];
      }

      interface MarkerOptions {
        position?: LatLng | LatLngLiteral;
        map?: Map;
        title?: string;
        icon?: string | Icon | Symbol;
      }

      interface InfoWindowOptions {
        content?: string | Element;
        position?: LatLng | LatLngLiteral;
      }

      interface LatLngLiteral {
        lat: number;
        lng: number;
      }

      interface Icon {
        url?: string;
        scaledSize?: Size;
        size?: Size;
        anchor?: Point;
      }

      interface Symbol {
        path: SymbolPath | string;
        scale?: number;
        fillColor?: string;
        fillOpacity?: number;
        strokeColor?: string;
        strokeWeight?: number;
        anchor?: Point;
      }

      interface Size {
        width: number;
        height: number;
      }

      interface Point {
        x: number;
        y: number;
      }

      interface MapTypeStyle {
        featureType?: string;
        elementType?: string;
        stylers?: Array<{ [key: string]: any }>;
      }
    }
  }
}

export {};
