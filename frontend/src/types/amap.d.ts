export {}

declare global {
  interface Window {
    AMap: typeof AMap
    _AMapSecurityConfig?: { securityJsCode: string }
  }

  namespace AMap {
    class Map {
      constructor(container: string | HTMLElement, opts?: MapOptions)
      destroy(): void
      setFitView(overlays?: any[], immediately?: boolean, avoid?: number[], maxZoom?: number): void
      add(overlay: any | any[]): void
      remove(overlay: any | any[]): void
      setCenter(center: [number, number]): void
      setZoom(zoom: number): void
      getCenter(): { lng: number; lat: number }
      getZoom(): number
      on(event: string, handler: Function): void
    }

    interface MapOptions {
      zoom?: number
      center?: [number, number]
      viewMode?: '2D' | '3D'
      mapStyle?: string
      resizeEnable?: boolean
    }

    class Marker {
      constructor(opts?: MarkerOptions)
      setPosition(pos: [number, number]): void
      setLabel(label: { content: string; offset?: { x: number; y: number } }): void
      setContent(content: string | HTMLElement): void
      on(event: string, handler: Function): void
      getPosition(): { lng: number; lat: number }
    }

    interface MarkerOptions {
      position?: [number, number]
      icon?: string | Icon
      content?: string | HTMLElement
      label?: { content: string; offset?: { x: number; y: number }; direction?: string }
      offset?: { x: number; y: number }
      zIndex?: number
    }

    class Icon {
      constructor(opts?: { size?: { w: number; h: number }; image?: string; imageSize?: { w: number; h: number } })
    }

    class InfoWindow {
      constructor(opts?: InfoWindowOptions)
      open(map: Map, pos?: [number, number]): void
      close(): void
      setContent(content: string | HTMLElement): void
    }

    interface InfoWindowOptions {
      content?: string | HTMLElement
      offset?: { x: number; y: number }
    }

    class Polyline {
      constructor(opts?: PolylineOptions)
      setPath(path: [number, number][]): void
      on(event: string, handler: Function): void
    }

    interface PolylineOptions {
      path?: [number, number][]
      strokeColor?: string
      strokeWeight?: number
      strokeOpacity?: number
      strokeStyle?: 'solid' | 'dashed'
      lineJoin?: 'miter' | 'round' | 'bevel'
      lineCap?: 'butt' | 'round' | 'square'
      showDir?: boolean
      zIndex?: number
    }

    class Pixel {
      constructor(x: number, y: number)
    }

    class Size {
      constructor(w: number, h: number)
    }
  }
}
