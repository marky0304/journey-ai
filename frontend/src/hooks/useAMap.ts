import { useEffect, useRef, useState } from 'react'

interface UseAMapResult {
  AMap: typeof window.AMap | null
  loaded: boolean
  error: string | null
}

let loadPromise: Promise<typeof window.AMap> | null = null

function loadAMap(): Promise<typeof window.AMap> {
  if (loadPromise) return loadPromise

  loadPromise = new Promise((resolve, reject) => {
    if (window.AMap) {
      resolve(window.AMap)
      return
    }

    const key = import.meta.env.VITE_AMAP_KEY
    const version = import.meta.env.VITE_AMAP_VERSION || '2.0'
    const securityCode = import.meta.env.VITE_AMAP_SECURITY_CODE

    if (!key || key === 'your_amap_key_here') {
      reject(new Error('VITE_AMAP_KEY 未配置，请前往 https://console.amap.com/dev/key/app 申请'))
      return
    }

    if (securityCode) {
      window._AMapSecurityConfig = { securityJsCode: securityCode }
    }

    const safetyPlugin = import.meta.env.DEV
      ? ''
      : '&plugin=AMap.Adapter'

    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=${version}&key=${key}${safetyPlugin}`
    script.onload = () => {
      if (window.AMap) {
        resolve(window.AMap)
      } else {
        reject(new Error('AMap 脚本已加载但 AMap 对象不可用'))
      }
    }
    script.onerror = () => reject(new Error('AMap 脚本加载失败'))
    document.head.appendChild(script)
  })

  return loadPromise
}

export function useAMap(): UseAMapResult {
  const [AMap, setAMap] = useState<typeof window.AMap | null>(null)
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const cancelledRef = useRef(false)

  useEffect(() => {
    cancelledRef.current = false

    loadAMap()
      .then((api) => {
        if (!cancelledRef.current) {
          setAMap(api)
          setLoaded(true)
        }
      })
      .catch((e) => {
        if (!cancelledRef.current) {
          setError(String(e))
        }
      })

    return () => {
      cancelledRef.current = true
    }
  }, [])

  return { AMap, loaded, error }
}
