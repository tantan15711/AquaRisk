import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from 'react'
import { useQuery } from '@tanstack/react-query'
import maplibregl from 'maplibre-gl'
import { create } from 'zustand'
import { isSupabaseConfigured, supabase } from './lib/supabase'
import {
  Bell,
  Cloud,
  CloudDrizzle,
  Clock3,
  CloudLightning,
  CloudSun,
  CloudRain,
  Droplets,
  Info,
  LocateFixed,
  MapPin,
  Moon,
  RefreshCcw,
  Route,
  ShieldAlert,
  Sun,
  ThermometerSun,
  Umbrella,
  Waves,
  Wind,
} from 'lucide-react'
import 'maplibre-gl/dist/maplibre-gl.css'
import './App.css'

type Coordinates = {
  latitude: number
  longitude: number
  accuracy?: number
  label: string
}

type WeatherResponse = {
  current?: {
    time?: string
    precipitation?: number
    rain?: number
    showers?: number
    temperature_2m?: number
    weather_code?: number
    wind_speed_10m?: number
  }
  hourly?: {
    time?: string[]
    temperature_2m?: number[]
    apparent_temperature?: number[]
    precipitation?: number[]
    precipitation_probability?: number[]
    relative_humidity_2m?: number[]
    weather_code?: number[]
    wind_direction_10m?: number[]
    wind_speed_10m?: number[]
  }
}

type FloodResponse = {
  daily?: {
    time?: string[]
    river_discharge?: number[]
    river_discharge_mean?: number[]
    river_discharge_max?: number[]
  }
}

type RiskLevel = 'Bajo' | 'Medio' | 'Alto' | 'Critico'
type Tone = 'safe' | 'watch' | 'warning' | 'danger'

type HourForecast = {
  time: string
  rain: number
  probability: number
  temperature?: number
  apparentTemperature?: number
  humidity?: number
  weatherCode?: number
  windDirection?: number
  windSpeed?: number
}

type HourRisk = {
  label: string
  tone: Tone
  advice: string
}

type RiskSummary = {
  level: RiskLevel
  score: number
  tone: Tone
  headline: string
  message: string
  rainLabel: string
  exitAdvice: string
  durationText: string
  thunderText: string
  thunderLikely: boolean
  timingText: string
  peakTimeText: string
}

type FloodSummary = {
  status: string
  detail: string
  tone: Tone
  dischargeText: string
}

type RainCell = {
  id: string
  areaLabel: string
  latitude: number
  longitude: number
  rainNext3h: number
  probability: number
  weatherCode?: number
  tone: Tone
  label: string
  score: number
}

type RainCellCollection = {
  type: 'FeatureCollection'
  features: Array<{
    type: 'Feature'
      properties: {
        id: string
        areaLabel: string
        label: string
      probability: number
      rainNext3h: number
      score: number
      tone: Tone
    }
    geometry: {
      type: 'Point'
      coordinates: [number, number]
    }
  }>
}

type SafePlace = {
  id: string
  name: string
  kind: string
  latitude: number
  longitude: number
  distanceKm: number
  source: string
}

type SafePlaceCollection = {
  type: 'FeatureCollection'
  features: Array<{
    type: 'Feature'
    properties: {
      id: string
      name: string
      kind: string
      distanceKm: number
    }
    geometry: {
      type: 'Point'
      coordinates: [number, number]
    }
  }>
}

type LocalRiskZone = {
  id: string
  name: string
  tone: Tone
  level: string
  detail: string
  distanceKm: number
}

type OverpassElement = {
  id: number
  type: string
  lat?: number
  lon?: number
  center?: {
    lat?: number
    lon?: number
  }
  tags?: Record<string, string>
}

type NominatimPlace = {
  place_id: number
  display_name?: string
  lat: string
  lon: string
  type?: string
}

type BackendSafeLocation = {
  id: string
  name: string
  kind: string
  source: string
  latitude: number
  longitude: number
  notes?: string | null
}

type BackendRiskZone = {
  id: string
  name: string
  source: string
  risk_level: 'bajo' | 'medio' | 'alto' | 'critico'
  latitude: number
  longitude: number
}

type RainViewerFrame = {
  time: number
  path: string
}

type RainViewerResponse = {
  host?: string
  radar?: {
    past?: RainViewerFrame[]
    nowcast?: RainViewerFrame[]
  }
}

type RadarFrame = {
  tileUrl: string
  observedAt: string
}

type LocalObservation = {
  kind: 'heavy-rain' | 'thunder'
  label: string
  expiresAt: number
}

type AquaStore = {
  location: Coordinates
  setLocation: (location: Coordinates) => void
  notificationPermission: NotificationPermission | 'unsupported'
  setNotificationPermission: (
    permission: NotificationPermission | 'unsupported',
  ) => void
}

const DEFAULT_LOCATION: Coordinates = {
  latitude: 19.4326,
  longitude: -99.1332,
  label: 'Zona de monitoreo inicial',
}

const THUNDER_CODES = new Set([95, 96, 99])

const useAquaStore = create<AquaStore>((set) => ({
  location: DEFAULT_LOCATION,
  setLocation: (location) => set({ location }),
  notificationPermission: getNotificationPermission(),
  setNotificationPermission: (notificationPermission) =>
    set({ notificationPermission }),
}))

function getNotificationApi() {
  if (typeof window === 'undefined' || !('Notification' in window)) return null
  return window.Notification
}

function getNotificationPermission(): NotificationPermission | 'unsupported' {
  const notificationApi = getNotificationApi()
  return notificationApi ? notificationApi.permission : 'unsupported'
}

async function getReadyServiceWorker() {
  if (
    typeof navigator === 'undefined' ||
    !('serviceWorker' in navigator) ||
    typeof window === 'undefined'
  ) {
    return undefined
  }

  try {
    return await Promise.race<ServiceWorkerRegistration | undefined>([
      navigator.serviceWorker.ready,
      new Promise((resolve) => {
        window.setTimeout(() => resolve(undefined), 1800)
      }),
    ])
  } catch {
    return undefined
  }
}

async function showAquaNotification(
  title: string,
  options: NotificationOptions = {},
) {
  const notificationApi = getNotificationApi()

  if (!notificationApi || notificationApi.permission !== 'granted') {
    return false
  }

  const registration = await getReadyServiceWorker()

  if (registration?.showNotification) {
    try {
      await registration.showNotification(title, options)
      return true
    } catch (error) {
      console.warn('No se pudo mostrar la notificacion con service worker.', error)
    }
  }

  try {
    new notificationApi(title, options)
    return true
  } catch (error) {
    console.warn('No se pudo mostrar la notificacion en este navegador.', error)
    return false
  }
}

async function fetchWeather(location: Coordinates): Promise<WeatherResponse> {
  const params = new URLSearchParams({
    latitude: String(location.latitude),
    longitude: String(location.longitude),
    current: 'temperature_2m,precipitation,rain,showers,weather_code,wind_speed_10m',
    hourly:
      'temperature_2m,apparent_temperature,precipitation,precipitation_probability,relative_humidity_2m,weather_code,wind_direction_10m,wind_speed_10m',
    forecast_days: '2',
    timezone: 'auto',
  })

  const response = await fetch(`https://api.open-meteo.com/v1/forecast?${params}`)

  if (!response.ok) {
    throw new Error('No se pudo consultar el clima')
  }

  return response.json()
}

async function fetchFlood(location: Coordinates): Promise<FloodResponse> {
  const params = new URLSearchParams({
    latitude: String(location.latitude),
    longitude: String(location.longitude),
    daily: 'river_discharge,river_discharge_mean,river_discharge_max',
    past_days: '7',
    forecast_days: '7',
    cell_selection: 'nearest',
  })

  const response = await fetch(`https://flood-api.open-meteo.com/v1/flood?${params}`)

  if (!response.ok) {
    throw new Error('No se pudo consultar el caudal del rio')
  }

  return response.json()
}

async function fetchRadarFrame(): Promise<RadarFrame | undefined> {
  const response = await fetch('https://api.rainviewer.com/public/weather-maps.json')

  if (!response.ok) {
    throw new Error('No se pudo consultar radar de lluvia')
  }

  const data = (await response.json()) as RainViewerResponse
  const frames = [
    ...(data.radar?.past ?? []),
    ...(data.radar?.nowcast ?? []),
  ].filter((frame) => frame.path)
  const latestFrame = frames.at(-1)

  if (!data.host || !latestFrame) return undefined

  return {
    tileUrl: `${data.host}${latestFrame.path}/256/{z}/{x}/{y}/2/1_1.png`,
    observedAt: new Date(latestFrame.time * 1000).toISOString(),
  }
}

function getDistanceKm(
  origin: Pick<Coordinates, 'latitude' | 'longitude'>,
  target: Pick<Coordinates, 'latitude' | 'longitude'>,
) {
  const earthRadiusKm = 6371
  const toRadians = (value: number) => (value * Math.PI) / 180
  const latDelta = toRadians(target.latitude - origin.latitude)
  const lonDelta = toRadians(target.longitude - origin.longitude)
  const startLat = toRadians(origin.latitude)
  const endLat = toRadians(target.latitude)
  const a =
    Math.sin(latDelta / 2) ** 2 +
    Math.cos(startLat) * Math.cos(endLat) * Math.sin(lonDelta / 2) ** 2

  return earthRadiusKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

function formatDistance(distanceKm: number) {
  if (distanceKm < 1) return `${Math.round(distanceKm * 1000)} m`
  return `${formatNumber(distanceKm, 1)} km`
}

function getSafePlaceKind(tags: Record<string, string> = {}) {
  const amenity = tags.amenity
  const emergency = tags.emergency

  if (emergency === 'assembly_point') return 'Punto de reunion'
  if (amenity === 'hospital') return 'Hospital'
  if (amenity === 'fire_station') return 'Bomberos'
  if (amenity === 'police') return 'Policia'
  if (amenity === 'community_centre') return 'Centro comunitario'
  if (amenity === 'townhall') return 'Gobierno local'
  if (amenity === 'school') return 'Escuela'
  return 'Punto de apoyo'
}

function getNominatimKind(query: string) {
  if (query === 'hospital') return 'Hospital'
  if (query === 'police') return 'Policia'
  if (query === 'fire station') return 'Bomberos'
  if (query === 'school') return 'Escuela'
  if (query === 'shelter') return 'Refugio'
  return 'Punto de apoyo'
}

async function fetchNominatimSafePlaces(location: Coordinates) {
  const delta = 0.035
  const viewbox = [
    location.longitude - delta,
    location.latitude + delta,
    location.longitude + delta,
    location.latitude - delta,
  ].join(',')
  const queries = ['hospital', 'police', 'fire station', 'school', 'shelter']
  const responses = await Promise.all(
    queries.map(async (query) => {
      const params = new URLSearchParams({
        format: 'jsonv2',
        q: query,
        limit: '3',
        bounded: '1',
        viewbox,
      })
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?${params}`,
      )
      if (!response.ok) return []
      const data = (await response.json()) as NominatimPlace[]
      return data.map((place) => ({
        place,
        query,
      }))
    }),
  )

  const places = new Map<string, SafePlace>()

  for (const item of responses.flat()) {
    const latitude = Number(item.place.lat)
    const longitude = Number(item.place.lon)
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) continue

    const kind = getNominatimKind(item.query)
    const name = item.place.display_name?.split(',')[0]?.trim() || kind
    const distanceKm = getDistanceKm(location, { latitude, longitude })

    places.set(`nominatim-${item.place.place_id}`, {
      id: `nominatim-${item.place.place_id}`,
      name,
      kind,
      latitude,
      longitude,
      distanceKm,
      source: 'OpenStreetMap',
    })
  }

  return [...places.values()]
    .sort((left, right) => left.distanceKm - right.distanceKm)
    .slice(0, 6)
}

async function fetchSafePlaces(location: Coordinates): Promise<SafePlace[]> {
  const supportAmenities =
    '^(hospital|fire_station|police|school|community_centre|townhall)$'
  const query = `
    [out:json][timeout:12];
    (
      node["amenity"~"${supportAmenities}"](around:3500,${location.latitude},${location.longitude});
      way["amenity"~"${supportAmenities}"](around:3500,${location.latitude},${location.longitude});
      relation["amenity"~"${supportAmenities}"](around:3500,${location.latitude},${location.longitude});
      node["emergency"="assembly_point"](around:3500,${location.latitude},${location.longitude});
      way["emergency"="assembly_point"](around:3500,${location.latitude},${location.longitude});
      relation["emergency"="assembly_point"](around:3500,${location.latitude},${location.longitude});
    );
    out center 24;
  `

  try {
    const response = await fetch(
      `https://overpass-api.de/api/interpreter?data=${encodeURIComponent(query)}`,
    )

    if (response.ok) {
      const data = (await response.json()) as { elements?: OverpassElement[] }
      const places = new Map<string, SafePlace>()

      for (const element of data.elements ?? []) {
        const latitude = element.lat ?? element.center?.lat
        const longitude = element.lon ?? element.center?.lon
        if (latitude === undefined || longitude === undefined) continue

        const kind = getSafePlaceKind(element.tags)
        const name = element.tags?.name?.trim() || kind
        const distanceKm = getDistanceKm(location, { latitude, longitude })

        places.set(`${element.type}-${element.id}`, {
          id: `${element.type}-${element.id}`,
          name,
          kind,
          latitude,
          longitude,
          distanceKm,
          source: 'OpenStreetMap',
        })
      }

      const overpassPlaces = [...places.values()]
        .sort((left, right) => left.distanceKm - right.distanceKm)
        .slice(0, 6)

      if (overpassPlaces.length > 0) return overpassPlaces
    }
  } catch {
    // Nominatim fallback below keeps the feature useful if Overpass is saturated.
  }

  return fetchNominatimSafePlaces(location)
}

async function fetchBackendSafePlaces(location: Coordinates): Promise<SafePlace[]> {
  if (!supabase) return []

  const { data, error } = await supabase
    .from('safe_location_points')
    .select('id,name,kind,source,latitude,longitude,notes,is_active')
    .eq('is_active', true)

  if (error) throw new Error(error.message)

  return ((data ?? []) as BackendSafeLocation[])
    .map((place) => ({
      id: `supabase-safe-${place.id}`,
      name: place.name,
      kind: place.kind,
      latitude: Number(place.latitude),
      longitude: Number(place.longitude),
      distanceKm: getDistanceKm(location, {
        latitude: Number(place.latitude),
        longitude: Number(place.longitude),
      }),
      source: place.source || 'Supabase',
    }))
    .filter((place) => Number.isFinite(place.distanceKm) && place.distanceKm <= 20)
    .sort((left, right) => left.distanceKm - right.distanceKm)
    .slice(0, 6)
}

async function fetchBackendRiskZones(): Promise<BackendRiskZone[]> {
  if (!supabase) return []

  const { data, error } = await supabase
    .from('official_risk_zone_centers')
    .select('id,name,source,risk_level,latitude,longitude')

  if (error) throw new Error(error.message)

  return (data ?? []) as BackendRiskZone[]
}

function getToneFromBackendRisk(riskLevel: BackendRiskZone['risk_level']): Tone {
  if (riskLevel === 'critico') return 'danger'
  if (riskLevel === 'alto') return 'warning'
  if (riskLevel === 'medio') return 'watch'
  return 'safe'
}

function buildBackendRiskZones(
  zones: BackendRiskZone[],
  location: Coordinates,
): LocalRiskZone[] {
  return zones
    .map((zone) => ({
      id: `official-${zone.id}`,
      name: zone.name,
      tone: getToneFromBackendRisk(zone.risk_level),
      level: `Zona ${zone.risk_level}`,
      detail: zone.source,
      distanceKm: getDistanceKm(location, {
        latitude: Number(zone.latitude),
        longitude: Number(zone.longitude),
      }),
    }))
    .filter((zone) => Number.isFinite(zone.distanceKm) && zone.distanceKm <= 20)
    .sort((left, right) => left.distanceKm - right.distanceKm)
    .slice(0, 4)
}

async function registerAlertSubscription(location: Coordinates) {
  if (!supabase) {
    throw new Error('Supabase no esta configurado')
  }

  const { error } = await supabase.from('alert_subscriptions').insert({
    device_label: location.label,
    point: `SRID=4326;POINT(${location.longitude} ${location.latitude})`,
    radius_m: Math.max(1500, Math.round(location.accuracy ?? 1500)),
    min_score: 58,
    is_active: true,
  })

  if (error) throw new Error(error.message)
}

function buildNearbyLocations(location: Coordinates) {
  const offsets = [
    [0, 0, 'Tu punto'],
    [0.018, 0, 'Norte'],
    [-0.018, 0, 'Sur'],
    [0, 0.018, 'Este'],
    [0, -0.018, 'Oeste'],
    [0.018, 0.018, 'Noreste'],
    [0.018, -0.018, 'Noroeste'],
    [-0.018, 0.018, 'Sureste'],
    [-0.018, -0.018, 'Suroeste'],
  ] as const

  return offsets.map(([latOffset, lngOffset, label]) => ({
    latitude: location.latitude + latOffset,
    longitude: location.longitude + lngOffset,
    label,
  }))
}

async function fetchNearbyRain(location: Coordinates): Promise<RainCell[]> {
  const points = buildNearbyLocations(location)

  const responses = await Promise.all(
    points.map(async (point, index) => {
      const weather = await fetchWeather({
        latitude: point.latitude,
        longitude: point.longitude,
        label: point.label,
      })
      const upcoming = getUpcomingHours(weather, 3)
      const rainNext3h = upcoming.reduce((total, hour) => total + hour.rain, 0)
      const probability = Math.max(...upcoming.map((hour) => hour.probability), 0)
      const weatherCode = upcoming.find((hour) => hour.weatherCode)?.weatherCode
      const score = Math.min(100, Math.round(rainNext3h * 12 + probability * 0.55))

      return {
        id: `cell-${index}`,
        areaLabel: point.label,
        latitude: point.latitude,
        longitude: point.longitude,
        rainNext3h,
        probability,
        weatherCode,
        tone: getToneFromScore(score, hasThunder(upcoming)),
        label: describeRain(rainNext3h / 3),
        score,
      }
    }),
  )

  return responses
}

function getRainNow(weather?: WeatherResponse) {
  const current = weather?.current
  return current?.precipitation ?? current?.rain ?? current?.showers ?? 0
}

function getCurrentIndex(weather?: WeatherResponse) {
  const times = weather?.hourly?.time ?? []
  const currentTime = weather?.current?.time
  if (!currentTime) return 0

  const index = times.findIndex((time) => time >= currentTime)
  return index >= 0 ? index : 0
}

function getUpcomingHours(weather?: WeatherResponse, hours = 12): HourForecast[] {
  return getHoursFromIndex(weather, getCurrentIndex(weather), hours)
}

function getMonitoringHours(weather?: WeatherResponse, hours = 4): HourForecast[] {
  return getHoursFromIndex(weather, Math.max(0, getCurrentIndex(weather) - 1), hours)
}

function getHoursFromIndex(
  weather: WeatherResponse | undefined,
  startIndex: number,
  hours: number,
): HourForecast[] {
  const hourly = weather?.hourly
  const times = hourly?.time ?? []
  const temperature = hourly?.temperature_2m ?? []
  const apparentTemperature = hourly?.apparent_temperature ?? []
  const precipitation = hourly?.precipitation ?? []
  const probability = hourly?.precipitation_probability ?? []
  const humidity = hourly?.relative_humidity_2m ?? []
  const weatherCodes = hourly?.weather_code ?? []
  const windDirection = hourly?.wind_direction_10m ?? []
  const windSpeed = hourly?.wind_speed_10m ?? []

  return times.slice(startIndex, startIndex + hours).map((time, offset) => {
    const index = startIndex + offset
    return {
      time,
      rain: precipitation[index] ?? 0,
      probability: probability[index] ?? 0,
      temperature: temperature[index],
      apparentTemperature: apparentTemperature[index],
      humidity: humidity[index],
      weatherCode: weatherCodes[index],
      windDirection: windDirection[index],
      windSpeed: windSpeed[index],
    }
  })
}

function mergeHours(...hourGroups: HourForecast[][]) {
  const byTime = new Map<string, HourForecast>()

  for (const hours of hourGroups) {
    for (const hour of hours) {
      byTime.set(hour.time, hour)
    }
  }

  return [...byTime.values()].sort(
    (left, right) => new Date(left.time).getTime() - new Date(right.time).getTime(),
  )
}

function hasThunder(hours: HourForecast[]) {
  return hours.some((hour) => THUNDER_CODES.has(hour.weatherCode ?? -1))
}

function getRainNextHours(weather?: WeatherResponse, hours = 6) {
  return getUpcomingHours(weather, hours).reduce(
    (total, hour) => total + Number(hour.rain || 0),
    0,
  )
}

function getProbability(weather?: WeatherResponse, hours = 6) {
  const upcoming = getUpcomingHours(weather, hours)
  return Math.max(...upcoming.map((hour) => hour.probability), 0)
}

function describeRain(mmPerHour: number) {
  if (mmPerHour < 0.2) return 'Sin lluvia'
  if (mmPerHour < 2.5) return 'Lluvia ligera'
  if (mmPerHour < 7.5) return 'Lluvia moderada'
  if (mmPerHour < 15) return 'Lluvia fuerte'
  return 'Lluvia muy fuerte'
}

function describeWeatherCode(code?: number) {
  if (code === undefined) return 'Sin dato'
  if (THUNDER_CODES.has(code)) return 'Tormenta electrica'
  if ([80, 81, 82].includes(code)) return 'Chubascos'
  if ([61, 63, 65].includes(code)) return 'Lluvia'
  if ([51, 53, 55].includes(code)) return 'Llovizna'
  if ([45, 48].includes(code)) return 'Niebla'
  if (code === 1) return 'Mayormente despejado'
  if (code === 2) return 'Nubes y claros'
  if (code === 3) return 'Nublado'
  if (code === 0) return 'Despejado'
  return 'Condicion variable'
}

function getHourRisk(hour: HourForecast): HourRisk {
  if (THUNDER_CODES.has(hour.weatherCode ?? -1)) {
    return {
      label: 'Tormenta',
      tone: 'danger',
      advice: 'Evita salir',
    }
  }

  if (hour.rain >= 15) {
    return {
      label: 'Muy fuerte',
      tone: 'danger',
      advice: 'Ruta segura',
    }
  }

  if (hour.rain >= 7.5) {
    return {
      label: 'Fuerte',
      tone: 'warning',
      advice: 'Precaucion',
    }
  }

  if (hour.rain >= 2.5) {
    return {
      label: 'Moderada',
      tone: 'watch',
      advice: 'Vigila calles bajas',
    }
  }

  if (hour.rain >= 1 && hour.probability >= 70) {
    return {
      label: 'Probable',
      tone: 'warning',
      advice: 'Espera si puedes',
    }
  }

  if (hour.rain >= 0.2 || hour.probability >= 60) {
    return {
      label: 'Posible',
      tone: 'watch',
      advice: 'Lleva paraguas',
    }
  }

  return {
    label: 'Baja',
    tone: 'safe',
    advice: 'Normal',
  }
}

function isNightTime(value?: string) {
  if (!value) return false
  const hour = new Date(value).getHours()
  return hour < 6 || hour >= 19
}

function getWeatherIcon(code?: number, time?: string) {
  const iconProps = { size: 22, 'aria-hidden': true } as const

  if (THUNDER_CODES.has(code ?? -1)) return <CloudLightning {...iconProps} />
  if ([80, 81, 82, 61, 63, 65].includes(code ?? -1)) {
    return <CloudRain {...iconProps} />
  }
  if ([51, 53, 55].includes(code ?? -1)) return <CloudDrizzle {...iconProps} />
  if ([45, 48].includes(code ?? -1)) return <Cloud {...iconProps} />
  if ([1, 2].includes(code ?? -1)) return <CloudSun {...iconProps} />
  if (code === 0) {
    return isNightTime(time) ? <Moon {...iconProps} /> : <Sun {...iconProps} />
  }
  return <Cloud {...iconProps} />
}

function getRainBarWidth(hour: HourForecast) {
  if (hour.rain <= 0 && hour.probability <= 0) return 2
  return Math.min(100, Math.max(4, hour.rain * 8 + hour.probability * 0.45))
}

function formatDirection(degrees?: number) {
  if (degrees === undefined) return 'Sin viento'
  const directions = ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO']
  return directions[Math.round(degrees / 45) % directions.length]
}

function getToneFromScore(score: number, thunderLikely = false): Tone {
  if (thunderLikely || score >= 78) return 'danger'
  if (score >= 58) return 'warning'
  if (score >= 32) return 'watch'
  return 'safe'
}

function getRiskLevel(score: number, thunderLikely = false): RiskLevel {
  if (thunderLikely || score >= 78) return 'Critico'
  if (score >= 58) return 'Alto'
  if (score >= 32) return 'Medio'
  return 'Bajo'
}

function getDurationText(hours: HourForecast[]) {
  const rainyIndex = hours.findIndex(
    (hour) => hour.rain >= 0.2 || hour.probability >= 55,
  )

  if (rainyIndex === -1) {
    return 'No se ve lluvia relevante en las proximas 12 h'
  }

  let duration = 0
  for (let index = rainyIndex; index < hours.length; index += 1) {
    const hour = hours[index]
    if (hour.rain < 0.2 && hour.probability < 55) break
    duration += 1
  }

  const startText = rainyIndex === 0 ? 'desde ahora' : `desde ${formatTime(hours[rainyIndex].time)}`
  return `Podria durar ${duration} h ${startText}`
}

function getPeakHour(hours: HourForecast[]) {
  return hours.reduce<HourForecast | undefined>((peak, hour) => {
    if (!peak || hour.rain > peak.rain) return hour
    return peak
  }, undefined)
}

function buildFloodSummary(flood?: FloodResponse): FloodSummary {
  const times = flood?.daily?.time ?? []
  const discharge = flood?.daily?.river_discharge ?? []
  const mean = flood?.daily?.river_discharge_mean ?? []
  const max = flood?.daily?.river_discharge_max ?? []

  if (times.length === 0 || discharge.length === 0) {
    return {
      status: 'Sin dato de rio',
      detail: 'No se encontro caudal cercano',
      tone: 'watch',
      dischargeText: 'Sin dato',
    }
  }

  const today = new Date().toISOString().slice(0, 10)
  const todayIndex = Math.max(0, times.findIndex((time) => time >= today))
  const current = discharge[todayIndex] ?? discharge[0] ?? 0
  const currentMean = mean[todayIndex] ?? current
  const nextMax = Math.max(...max.slice(todayIndex, todayIndex + 7), current)
  const ratio = currentMean > 0 ? nextMax / currentMean : 1

  if (ratio >= 2.2 || nextMax >= 150) {
    return {
      status: 'Rio muy elevado',
      detail: `Modelo GloFAS: max. ${formatNumber(nextMax)} m3/s`,
      tone: 'danger',
      dischargeText: `${formatNumber(current)} m3/s`,
    }
  }

  if (ratio >= 1.5 || nextMax >= 75) {
    return {
      status: 'Caudal en vigilancia',
      detail: `Modelo GloFAS: max. ${formatNumber(nextMax)} m3/s`,
      tone: 'warning',
      dischargeText: `${formatNumber(current)} m3/s`,
    }
  }

  return {
    status: 'Rio estable',
    detail: `Modelo GloFAS dentro de rango cercano`,
    tone: 'safe',
    dischargeText: `${formatNumber(current)} m3/s`,
  }
}

function buildRiskSummary(weather?: WeatherResponse): RiskSummary {
  const rainNow = getRainNow(weather)
  const upcoming12 = getUpcomingHours(weather, 12)
  const monitoringHours = getMonitoringHours(weather, 5)
  const riskWindow = mergeHours(monitoringHours, upcoming12)
  const immediateHours = getUpcomingHours(weather, 3)
  const rainNext3 = getRainNextHours(weather, 3)
  const rainNext6 = getRainNextHours(weather, 6)
  const immediateProbability = Math.max(
    getProbability(weather, 3),
    ...monitoringHours.map((hour) => hour.probability),
    0,
  )
  const dayProbability = getProbability(weather, 12)
  const maxRainHour = Math.max(...upcoming12.map((hour) => hour.rain), rainNow)
  const peakHour = getPeakHour(riskWindow)
  const thunderSoon = hasThunder(monitoringHours)
  const thunderLater = hasThunder(upcoming12)
  const immediatePeak = Math.max(...monitoringHours.map((hour) => hour.rain), rainNow)
  const activeRainSignal =
    rainNow >= 0.2 || (immediateHours[0]?.rain ?? 0) >= 0.2
  const highProbabilityRain = activeRainSignal && immediateProbability >= 65
  const recentHeavySignal = immediatePeak >= 7.5 || thunderSoon
  const immediateScore = Math.min(
    100,
    Math.round(
      rainNow * 12 +
        immediatePeak * 10 +
        rainNext3 * 6 +
        immediateProbability * 0.35 +
        (thunderSoon ? 22 : 0) +
        (highProbabilityRain ? 10 : 0),
    ),
  )
  const forecastScore = Math.min(
    100,
    Math.round(
      maxRainHour * 6 +
        rainNext6 * 3 +
        dayProbability * 0.25 +
        (thunderLater ? 18 : 0),
    ),
  )
  const hasLaterRisk = forecastScore >= 45 && immediateScore < 45
  const score = Math.max(immediateScore, highProbabilityRain ? 58 : 0)
  const level = getRiskLevel(score, thunderSoon)
  const tone = getToneFromScore(score, thunderSoon)
  const rainLabel = describeRain(Math.max(rainNow, maxRainHour, immediatePeak))
  const durationText = getDurationText(upcoming12)
  const peakTimeText =
    peakHour && peakHour.rain >= 0.2
      ? `Pico cercano: ${formatTime(peakHour.time)} (ventana +-1 h)`
      : 'Sin pico relevante'
  const timingText = recentHeavySignal
    ? 'Tormentas y chubascos pueden recorrerse 30-60 min.'
    : hasLaterRisk
      ? 'Riesgo bajo ahora; vigilancia por lluvia mas tarde.'
      : highProbabilityRain
        ? 'Hay lluvia activa o muy probable; usa esta hora como ventana aproximada.'
        : 'Riesgo calculado para este momento y las proximas horas.'

  if (hasLaterRisk) {
    return {
      level,
      score,
      tone,
      headline: 'Ahora tranquilo; vigila mas tarde',
      message: 'No se detecta lluvia fuerte en este momento, pero el pronostico marca lluvia mas adelante.',
      rainLabel,
      exitAdvice: 'Puedes salir ahora; vuelve a revisar antes de la hora de lluvia.',
      durationText,
      thunderText: thunderLater ? 'Truenos posibles mas tarde' : 'Sin truenos inmediatos',
      thunderLikely: thunderLater,
      timingText,
      peakTimeText,
    }
  }

  if (thunderSoon || score >= 78) {
    return {
      level,
      score,
      tone,
      headline: 'Mejor evita salir',
      message: 'Hay senales de lluvia pesada o tormenta; prioriza rutas seguras.',
      rainLabel,
      exitAdvice: 'No recomendado salir si no es necesario.',
      durationText,
      thunderText: thunderSoon ? 'Posibles truenos ahora' : 'Sin truenos detectados',
      thunderLikely: thunderSoon,
      timingText,
      peakTimeText,
    }
  }

  if (score >= 58) {
    return {
      level,
      score,
      tone,
      headline: highProbabilityRain
        ? 'Espera si puedes'
        : 'Sal solo con precaucion',
      message: highProbabilityRain
        ? 'Hay lluvia activa o muy probable; el pico puede moverse dentro de esta hora.'
        : 'Puede haber lluvia fuerte, charcos grandes o baja visibilidad.',
      rainLabel,
      exitAdvice: highProbabilityRain
        ? 'Si no es urgente, espera a que baje la lluvia.'
        : 'Evita zonas bajas y revisa una ruta alterna.',
      durationText,
      thunderText: 'Sin truenos fuertes detectados',
      thunderLikely: thunderSoon,
      timingText,
      peakTimeText,
    }
  }

  if (score >= 32) {
    return {
      level,
      score,
      tone,
      headline: 'Precaucion moderada',
      message: 'La lluvia no parece extrema, pero conviene monitorear cambios.',
      rainLabel,
      exitAdvice: activeRainSignal
        ? 'Sal solo si es necesario y revisa el cielo.'
        : 'Puedes salir, pero revisa el mapa antes.',
      durationText,
      thunderText: 'Sin truenos fuertes detectados',
      thunderLikely: thunderSoon,
      timingText,
      peakTimeText,
    }
  }

  return {
    level,
    score,
    tone,
    headline: 'Puedes salir con normalidad',
    message: 'No se detecta lluvia importante en las proximas horas.',
    rainLabel,
    exitAdvice: 'Riesgo bajo por ahora.',
    durationText,
    thunderText: 'Sin truenos detectados',
    thunderLikely: thunderSoon,
    timingText,
    peakTimeText,
  }
}

function buildObservedRiskSummary(
  baseRisk: RiskSummary,
  observation: LocalObservation | null,
): RiskSummary {
  if (!observation) return baseRisk

  const isThunder = observation.kind === 'thunder'

  return {
    ...baseRisk,
    level: isThunder ? 'Critico' : 'Alto',
    score: Math.max(baseRisk.score, isThunder ? 92 : 82),
    tone: isThunder ? 'danger' : 'warning',
    headline: isThunder ? 'Mejor evita salir' : 'Lluvia fuerte reportada',
    message: isThunder
      ? 'Tu observacion local reporta truenos; toma prioridad sobre el pronostico horario.'
      : 'Tu observacion local reporta lluvia fuerte; evita zonas bajas y espera si puedes.',
    rainLabel: isThunder ? 'Tormenta reportada' : 'Lluvia fuerte reportada',
    exitAdvice: isThunder
      ? 'No salgas si no es necesario.'
      : 'Si no es urgente, espera a que baje la lluvia.',
    thunderText: isThunder ? 'Truenos reportados ahora' : baseRisk.thunderText,
    thunderLikely: isThunder || baseRisk.thunderLikely,
    timingText:
      'Prioridad a observacion local: el modelo puede ir atrasado en tormentas.',
    peakTimeText: 'Observacion local activa',
  }
}

function buildRainCellCollection(cells: RainCell[]): RainCellCollection {
  return {
    type: 'FeatureCollection',
    features: cells.map((cell) => ({
      type: 'Feature',
      properties: {
        id: cell.id,
        areaLabel: cell.areaLabel,
        label: cell.label,
        probability: cell.probability,
        rainNext3h: cell.rainNext3h,
        score: cell.score,
        tone: cell.tone,
      },
      geometry: {
        type: 'Point',
        coordinates: [cell.longitude, cell.latitude],
      },
    })),
  }
}

function buildSafePlaceCollection(places: SafePlace[]): SafePlaceCollection {
  return {
    type: 'FeatureCollection',
    features: places.map((place) => ({
      type: 'Feature',
      properties: {
        id: place.id,
        name: place.name,
        kind: place.kind,
        distanceKm: place.distanceKm,
      },
      geometry: {
        type: 'Point',
        coordinates: [place.longitude, place.latitude],
      },
    })),
  }
}

function buildLocalRiskZones(
  cells: RainCell[],
  flood: FloodSummary,
  location: Coordinates,
): LocalRiskZone[] {
  const riskyCells: LocalRiskZone[] = cells
    .filter((cell) => cell.score >= 32 || cell.rainNext3h >= 0.8)
    .sort((left, right) => right.score - left.score)
    .slice(0, 4)
    .map((cell) => ({
      id: cell.id,
      name: cell.areaLabel,
      tone: cell.tone,
      level: getRiskLevel(cell.score, THUNDER_CODES.has(cell.weatherCode ?? -1)),
      detail: `${formatNumber(cell.rainNext3h)} mm en 3 h | ${cell.probability}% prob.`,
      distanceKm: getDistanceKm(location, {
        latitude: cell.latitude,
        longitude: cell.longitude,
      }),
    }))

  if (flood.tone !== 'safe') {
    riskyCells.unshift({
      id: 'nearby-river',
      name: 'Rio cercano',
      tone: flood.tone,
      level: flood.status,
      detail: `${flood.dischargeText} | ${flood.detail}`,
      distanceKm: 0,
    })
  }

  return riskyCells
}

function formatNumber(value: number, digits = 1) {
  return new Intl.NumberFormat('es-MX', {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value)
}

function formatTime(value?: string) {
  if (!value) return 'Sin dato'

  return new Intl.DateTimeFormat('es-MX', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function formatTemperature(value?: number) {
  if (value === undefined) return 'Sin dato'
  return `${formatNumber(value, 0)}°`
}

function formatDayLabel(value?: string) {
  if (!value) return 'Sin dia'

  const date = new Date(value)
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(today.getDate() + 1)
  const key = (item: Date) => item.toLocaleDateString('es-MX')

  if (key(date) === key(today)) return 'Hoy'
  if (key(date) === key(tomorrow)) return 'Manana'

  return new Intl.DateTimeFormat('es-MX', {
    weekday: 'short',
  }).format(date)
}

function formatNotificationStatus(
  permission: NotificationPermission | 'unsupported',
) {
  if (permission === 'granted') return 'activadas'
  if (permission === 'denied') return 'bloqueadas'
  if (permission === 'unsupported') return 'no disponibles'
  return 'pendientes'
}

const RADAR_SOURCE_ID = 'rainviewer-radar'
const RADAR_LAYER_ID = 'rainviewer-radar-layer'

function syncRadarLayer(activeMap: maplibregl.Map, radarFrame?: RadarFrame) {
  if (activeMap.getLayer(RADAR_LAYER_ID)) {
    activeMap.removeLayer(RADAR_LAYER_ID)
  }

  if (activeMap.getSource(RADAR_SOURCE_ID)) {
    activeMap.removeSource(RADAR_SOURCE_ID)
  }

  if (!radarFrame) return

  activeMap.addSource(RADAR_SOURCE_ID, {
    type: 'raster',
    tiles: [radarFrame.tileUrl],
    tileSize: 256,
    attribution: 'RainViewer',
  })

  activeMap.addLayer(
    {
      id: RADAR_LAYER_ID,
      type: 'raster',
      source: RADAR_SOURCE_ID,
      paint: {
        'raster-opacity': 0.48,
        'raster-fade-duration': 0,
      },
    },
    activeMap.getLayer('rain-cell-circle') ? 'rain-cell-circle' : undefined,
  )
}

function RiskMap({
  location,
  rainCells,
  safePlaces,
  radarFrame,
}: {
  location: Coordinates
  rainCells: RainCellCollection
  safePlaces: SafePlaceCollection
  radarFrame?: RadarFrame
}) {
  const mapContainer = useRef<HTMLDivElement | null>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const marker = useRef<maplibregl.Marker | null>(null)
  const initialLocation = useRef(location)
  const initialRainCells = useRef(rainCells)
  const initialSafePlaces = useRef(safePlaces)
  const initialRadarFrame = useRef(radarFrame)

  useEffect(() => {
    if (!mapContainer.current || map.current) return

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: 'OpenStreetMap',
          },
        },
        layers: [
          {
            id: 'osm',
            type: 'raster',
            source: 'osm',
          },
        ],
      },
      center: [
        initialLocation.current.longitude,
        initialLocation.current.latitude,
      ],
      zoom: 12.5,
      attributionControl: { compact: true },
    })

    map.current.addControl(
      new maplibregl.NavigationControl({ showCompass: false }),
      'top-right',
    )

    marker.current = new maplibregl.Marker({ color: '#101820' })
      .setLngLat([
        initialLocation.current.longitude,
        initialLocation.current.latitude,
      ])
      .addTo(map.current)

    map.current.on('load', () => {
      map.current?.addSource('rain-cells', {
        type: 'geojson',
        data: initialRainCells.current,
      })
      map.current?.addSource('safe-places', {
        type: 'geojson',
        data: initialSafePlaces.current,
      })

      syncRadarLayer(map.current!, initialRadarFrame.current)

      map.current?.addLayer({
        id: 'rain-cell-circle',
        type: 'circle',
        source: 'rain-cells',
        paint: {
          'circle-color': [
            'match',
            ['get', 'tone'],
            'danger',
            '#dc2626',
            'warning',
            '#f97316',
            'watch',
            '#eab308',
            '#14b8a6',
          ],
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['get', 'score'],
            0,
            13,
            100,
            34,
          ],
          'circle-opacity': 0.58,
          'circle-stroke-color': '#101820',
          'circle-stroke-width': 2,
        },
      })

      map.current?.addLayer({
        id: 'safe-place-circle',
        type: 'circle',
        source: 'safe-places',
        paint: {
          'circle-color': '#0284c7',
          'circle-radius': 8,
          'circle-opacity': 0.86,
          'circle-stroke-color': '#ffffff',
          'circle-stroke-width': 3,
        },
      })

      map.current?.addLayer({
        id: 'safe-place-label',
        type: 'symbol',
        source: 'safe-places',
        layout: {
          'text-field': ['get', 'kind'],
          'text-size': 11,
          'text-offset': [0, 1.25],
          'text-anchor': 'top',
        },
        paint: {
          'text-color': '#075985',
          'text-halo-color': '#ffffff',
          'text-halo-width': 1.4,
        },
      })

      map.current?.on('click', 'rain-cell-circle', (event) => {
        const feature = event.features?.[0]
        const coordinates = feature?.geometry.type === 'Point'
          ? feature.geometry.coordinates
          : undefined

        if (!feature || !coordinates) return

        new maplibregl.Popup()
          .setLngLat(coordinates as [number, number])
          .setHTML(
            `<strong>${feature.properties?.label}</strong><br/>` +
              `${formatNumber(Number(feature.properties?.rainNext3h ?? 0))} mm en 3 h<br/>` +
              `${feature.properties?.probability ?? 0}% probabilidad`,
          )
          .addTo(map.current!)
      })

      map.current?.on('click', 'safe-place-circle', (event) => {
        const feature = event.features?.[0]
        const coordinates = feature?.geometry.type === 'Point'
          ? feature.geometry.coordinates
          : undefined

        if (!feature || !coordinates) return

        new maplibregl.Popup()
          .setLngLat(coordinates as [number, number])
          .setHTML(
            `<strong>${feature.properties?.name}</strong><br/>` +
              `${feature.properties?.kind}<br/>` +
              `${formatDistance(Number(feature.properties?.distanceKm ?? 0))} aprox.`,
          )
          .addTo(map.current!)
      })
    })

    return () => {
      map.current?.remove()
      map.current = null
      marker.current = null
    }
  }, [])

  useEffect(() => {
    const activeMap = map.current
    if (!activeMap) return

    const nextCenter: [number, number] = [location.longitude, location.latitude]
    marker.current?.setLngLat(nextCenter)
    activeMap.flyTo({ center: nextCenter, zoom: 13, essential: true })

    const updateMapData = () => {
      const source = activeMap.getSource('rain-cells') as
        | maplibregl.GeoJSONSource
        | undefined
      source?.setData(rainCells)

      const safeSource = activeMap.getSource('safe-places') as
        | maplibregl.GeoJSONSource
        | undefined
      safeSource?.setData(safePlaces)

      syncRadarLayer(activeMap, radarFrame)
    }

    if (activeMap.isStyleLoaded()) {
      updateMapData()
    } else {
      activeMap.once('load', updateMapData)
    }
  }, [location, rainCells, safePlaces, radarFrame])

  return <div ref={mapContainer} className="risk-map" aria-label="Mapa de lluvia" />
}

function MetricCard({
  icon,
  label,
  value,
  detail,
}: {
  icon: ReactNode
  label: string
  value: string
  detail: string
}) {
  return (
    <article className="metric-card">
      <div className="metric-icon">{icon}</div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </article>
  )
}

function App() {
  const { location, setLocation, notificationPermission, setNotificationPermission } =
    useAquaStore()
  const [locationMessage, setLocationMessage] = useState('')
  const [alertMessage, setAlertMessage] = useState('')
  const [isLocating, setIsLocating] = useState(false)
  const [localObservation, setLocalObservation] =
    useState<LocalObservation | null>(null)
  const lastAutoAlertRef = useRef('')

  const weatherQuery = useQuery({
    queryKey: ['weather', location.latitude.toFixed(4), location.longitude.toFixed(4)],
    queryFn: () => fetchWeather(location),
    staleTime: 1000 * 60 * 5,
    retry: 1,
  })

  const nearbyQuery = useQuery({
    queryKey: [
      'nearby-rain',
      location.latitude.toFixed(3),
      location.longitude.toFixed(3),
    ],
    queryFn: () => fetchNearbyRain(location),
    staleTime: 1000 * 60 * 8,
    retry: 1,
  })

  const floodQuery = useQuery({
    queryKey: [
      'flood',
      location.latitude.toFixed(3),
      location.longitude.toFixed(3),
    ],
    queryFn: () => fetchFlood(location),
    staleTime: 1000 * 60 * 30,
    retry: 1,
  })

  const radarQuery = useQuery({
    queryKey: ['rainviewer-radar'],
    queryFn: fetchRadarFrame,
    staleTime: 1000 * 60 * 4,
    refetchInterval: 1000 * 60 * 5,
    retry: 1,
  })

  const osmSafePlacesQuery = useQuery({
    queryKey: [
      'osm-safe-places',
      location.latitude.toFixed(3),
      location.longitude.toFixed(3),
    ],
    queryFn: () => fetchSafePlaces(location),
    staleTime: 1000 * 60 * 45,
    retry: 1,
  })

  const backendSafePlacesQuery = useQuery({
    queryKey: [
      'backend-safe-places',
      location.latitude.toFixed(3),
      location.longitude.toFixed(3),
    ],
    queryFn: () => fetchBackendSafePlaces(location),
    enabled: isSupabaseConfigured,
    staleTime: 1000 * 60 * 10,
    retry: 1,
  })

  const backendRiskZonesQuery = useQuery({
    queryKey: ['backend-risk-zones'],
    queryFn: fetchBackendRiskZones,
    enabled: isSupabaseConfigured,
    staleTime: 1000 * 60 * 10,
    retry: 1,
  })

  const activeObservation =
    localObservation && localObservation.expiresAt > Date.now()
      ? localObservation
      : null
  const weather = weatherQuery.data
  const baseRisk = useMemo(() => buildRiskSummary(weather), [weather])
  const risk = useMemo(
    () => buildObservedRiskSummary(baseRisk, activeObservation),
    [baseRisk, activeObservation],
  )
  const flood = useMemo(() => buildFloodSummary(floodQuery.data), [floodQuery.data])
  const rainCells = useMemo(
    () => buildRainCellCollection(nearbyQuery.data ?? []),
    [nearbyQuery.data],
  )
  const safePlaces = useMemo(() => {
    const places = [
      ...(backendSafePlacesQuery.data ?? []),
      ...(osmSafePlacesQuery.data ?? []),
    ]
    const byNameAndKind = new Map<string, SafePlace>()

    for (const place of places) {
      const key = `${place.name.toLowerCase()}-${place.kind.toLowerCase()}`
      const previous = byNameAndKind.get(key)
      if (!previous || place.distanceKm < previous.distanceKm) {
        byNameAndKind.set(key, place)
      }
    }

    return [...byNameAndKind.values()]
      .sort((left, right) => left.distanceKm - right.distanceKm)
      .slice(0, 6)
  }, [backendSafePlacesQuery.data, osmSafePlacesQuery.data])
  const safePlaceCollection = useMemo(
    () => buildSafePlaceCollection(safePlaces),
    [safePlaces],
  )
  const riskZones = useMemo(
    () => [
      ...buildBackendRiskZones(backendRiskZonesQuery.data ?? [], location),
      ...buildLocalRiskZones(nearbyQuery.data ?? [], flood, location),
    ].slice(0, 6),
    [backendRiskZonesQuery.data, nearbyQuery.data, flood, location],
  )
  const rainNow = getRainNow(weather)
  const rainNext6 = getRainNextHours(weather)
  const probability = getProbability(weather)
  const upcoming12 = getUpcomingHours(weather, 12)
  const nextHours = getUpcomingHours(weather, 24)
  const alertHour = useMemo(
    () =>
      nextHours.find(
        (hour) =>
          THUNDER_CODES.has(hour.weatherCode ?? -1) ||
          hour.rain >= 7.5 ||
          (hour.rain >= 2.5 && hour.probability >= 70),
      ),
    [nextHours],
  )
  const maxRainHour = Math.max(...upcoming12.map((hour) => hour.rain), rainNow)
  const currentWeatherText = describeWeatherCode(weather?.current?.weather_code)
  const isSafePlacesLoading =
    osmSafePlacesQuery.isLoading || backendSafePlacesQuery.isLoading
  const hasSafePlacesError =
    osmSafePlacesQuery.isError && safePlaces.length === 0

  useEffect(() => {
    if (!localObservation) return

    const timeout = window.setTimeout(() => {
      setLocalObservation((current) =>
        current && current.expiresAt <= Date.now() ? null : current,
      )
    }, Math.max(1000, localObservation.expiresAt - Date.now()))

    return () => window.clearTimeout(timeout)
  }, [localObservation])

  const reportLocalObservation = (kind: LocalObservation['kind']) => {
    setLocalObservation({
      kind,
      label: kind === 'thunder' ? 'Truenos ahora' : 'Lluvia fuerte ahora',
      expiresAt: Date.now() + 1000 * 60 * 90,
    })
  }

  const requestLocation = () => {
    if (!navigator.geolocation) {
      setLocationMessage('Tu navegador no tiene geolocalizacion disponible.')
      return
    }

    setIsLocating(true)
    setLocationMessage('')

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          label: 'Mi ubicacion actual',
        })
        setLocationMessage('Ubicacion actualizada con datos reales del clima.')
        setIsLocating(false)
      },
      () => {
        setLocationMessage('No se pudo obtener tu ubicacion.')
        setIsLocating(false)
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 1000 * 60 * 2,
      },
    )
  }

  const requestNotifications = async () => {
    const notificationApi = getNotificationApi()

    if (!notificationApi) {
      setNotificationPermission('unsupported')
      setAlertMessage('Este navegador no permite alertas preventivas.')
      return
    }

    let permission: NotificationPermission

    try {
      permission = await notificationApi.requestPermission()
    } catch {
      setAlertMessage('No se pudo pedir permiso de notificaciones en este navegador.')
      return
    }

    setNotificationPermission(permission)

    if (permission === 'granted') {
      const wasShown = await showAquaNotification('AquaRisk activado', {
        body: 'Recibiras avisos preventivos mientras AquaRisk este activo.',
      })

      if (isSupabaseConfigured) {
        try {
          await registerAlertSubscription(location)
          setAlertMessage('Alertas preventivas activadas para esta zona.')
        } catch {
          setAlertMessage(
            'Alertas del navegador activadas; la revision en segundo plano queda pendiente.',
          )
        }
      } else {
        setAlertMessage('Alertas del navegador activadas en esta version local.')
      }

      if (!wasShown) {
        setAlertMessage(
          'Permiso activado. Si tu celular bloquea la ventana de alerta, AquaRisk seguira avisando dentro de la app.',
        )
      }
    } else if (permission === 'denied') {
      setAlertMessage('Las alertas estan bloqueadas en este navegador.')
    } else {
      setAlertMessage('Las alertas quedaron pendientes de permiso.')
    }
  }

  useEffect(() => {
    if (notificationPermission !== 'granted') return

    const shouldAlert =
      risk.score >= 58 ||
      Boolean(alertHour) ||
      flood.tone === 'warning' ||
      flood.tone === 'danger'

    if (!shouldAlert) return

    const alertKey = [
      location.latitude.toFixed(3),
      location.longitude.toFixed(3),
      risk.level,
      risk.score,
      alertHour?.time ?? 'now',
      flood.status,
    ].join('|')

    if (lastAutoAlertRef.current === alertKey) return
    lastAutoAlertRef.current = alertKey

    const alertBody = alertHour
      ? `${describeRain(alertHour.rain)} probable a las ${formatTime(alertHour.time)}. Revisa zonas bajas y puntos seguros.`
      : `${risk.exitAdvice} ${flood.status}.`

    void showAquaNotification('AquaRisk: aviso preventivo', {
      body: alertBody,
      tag: 'aquarisk-auto-alert',
    })
  }, [alertHour, flood.status, flood.tone, location, notificationPermission, risk])

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <div className="brand-mark">
            <Waves size={26} aria-hidden="true" />
          </div>
          <div>
            <span>AquaRisk</span>
            <h1>Monitoreo de lluvia e inundacion</h1>
          </div>
        </div>

        <div className="header-actions">
          <button type="button" onClick={requestLocation} disabled={isLocating}>
            <LocateFixed size={18} aria-hidden="true" />
            {isLocating ? 'Ubicando' : 'Mi ubicacion'}
          </button>
          <button type="button" onClick={requestNotifications}>
            <Bell size={18} aria-hidden="true" />
            Alertas
          </button>
        </div>
      </header>

      <main className="dashboard">
        <section className={`risk-hero ${risk.tone}`} aria-live="polite">
          <div>
            <span className="section-kicker">Decision rapida</span>
            <strong>{risk.headline}</strong>
            <p>{risk.message}</p>
            <div className="risk-tags">
              <span>Pico futuro: {risk.rainLabel}</span>
              <span>{risk.thunderText}</span>
              <span>{risk.peakTimeText}</span>
              <span>{risk.durationText}</span>
            </div>
          </div>
          <div
            className={`score-meter ${risk.tone}`}
            style={{ '--score-angle': `${risk.score * 3.6}deg` } as CSSProperties}
            aria-label={`Riesgo actual ${risk.score} de 100`}
          >
            <span>{risk.score}/100</span>
            <small>riesgo ahora</small>
          </div>
        </section>

        <section className="map-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">Mapa</span>
              <h2>{location.label}</h2>
            </div>
            <button
              type="button"
              className="icon-button"
              onClick={() => {
                weatherQuery.refetch()
                nearbyQuery.refetch()
                floodQuery.refetch()
                radarQuery.refetch()
              }}
              aria-label="Actualizar datos"
            >
              <RefreshCcw size={18} aria-hidden="true" />
            </button>
          </div>

          <RiskMap
            location={location}
            rainCells={rainCells}
            safePlaces={safePlaceCollection}
            radarFrame={radarQuery.data}
          />

          <div className="legend">
            <span>
              <i className="legend-dot safe-dot" /> Baja
            </span>
            <span>
              <i className="legend-dot watch-dot" /> Vigilar
            </span>
            <span>
              <i className="legend-dot warning-dot" /> Fuerte
            </span>
            <span>
              <i className="legend-dot danger-dot" /> Tormenta
            </span>
            <span>
              <i className="legend-dot support-dot" /> Punto seguro
            </span>
          </div>
          <p className="map-note">
            Los circulos se calculan con Open-Meteo cerca de tu ubicacion. La
            capa de radar usa RainViewer cuando esta disponible. Los puntos
            seguros vienen de OpenStreetMap y deben confirmarse con autoridades.
          </p>
        </section>

        <aside className="insight-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">Condiciones</span>
              <h2>Lectura clara</h2>
            </div>
          </div>

          <div className="metric-grid">
            <MetricCard
              icon={<CloudRain size={20} aria-hidden="true" />}
              label="Lluvia ahora"
              value={describeRain(rainNow)}
              detail={`${formatNumber(rainNow)} mm/h aprox. | ${currentWeatherText}`}
            />
            <MetricCard
              icon={<Droplets size={20} aria-hidden="true" />}
              label="Acumulado 6 h"
              value={`${formatNumber(rainNext6)} mm`}
              detail={`${probability}% probabilidad maxima`}
            />
            <MetricCard
              icon={<CloudRain size={20} aria-hidden="true" />}
              label="Radar"
              value={radarQuery.data ? 'Capa activa' : 'Sin radar'}
              detail={
                radarQuery.data
                  ? `Ultima imagen: ${formatTime(radarQuery.data.observedAt)}`
                  : 'RainViewer no devolvio imagen reciente'
              }
            />
            <MetricCard
              icon={<CloudLightning size={20} aria-hidden="true" />}
              label="Truenos"
              value={risk.thunderLikely ? 'Posibles' : 'No inmediatos'}
              detail={risk.timingText}
            />
            <MetricCard
              icon={<Clock3 size={20} aria-hidden="true" />}
              label="Duracion"
              value={risk.durationText}
              detail={`Pico esperado: ${formatNumber(maxRainHour)} mm/h`}
            />
            <MetricCard
              icon={<Waves size={20} aria-hidden="true" />}
              label="Rio cercano"
              value={flood.status}
              detail={`${flood.dischargeText} | ${flood.detail}`}
            />
            <MetricCard
              icon={<Route size={20} aria-hidden="true" />}
              label="Salir"
              value={risk.exitAdvice}
              detail={`Nivel de riesgo: ${risk.level} | ${risk.timingText}`}
            />
            <MetricCard
              icon={<MapPin size={20} aria-hidden="true" />}
              label="GPS"
              value={
                location.accuracy
                  ? `${Math.round(location.accuracy)} m`
                  : 'Ubicacion base'
              }
              detail={`${formatNumber(location.latitude, 3)}, ${formatNumber(
                location.longitude,
                3,
              )}`}
            />
          </div>

          <div className="explain-box">
            <Info size={17} aria-hidden="true" />
            <p>
              1 mm de lluvia significa 1 litro de agua por metro cuadrado. Por
              eso AquaRisk tambien lo traduce a ligera, moderada o fuerte.
            </p>
          </div>

          <div className="observation-box">
            <div>
              <span className="section-kicker">Observacion local</span>
              <h3>Lo que ves ahora</h3>
              <p>
                Si la tormenta ya esta encima y el modelo va atrasado, marca una
                senal temporal para priorizar tu observacion.
              </p>
            </div>
            <div className="observation-actions">
              <button
                type="button"
                onClick={() => reportLocalObservation('heavy-rain')}
              >
                Lluvia fuerte
              </button>
              <button type="button" onClick={() => reportLocalObservation('thunder')}>
                Truenos
              </button>
              <button type="button" onClick={() => setLocalObservation(null)}>
                Limpiar
              </button>
            </div>
            {activeObservation && (
              <small>
                Activo: {activeObservation.label}. AquaRisk dara prioridad a este
                reporte por 90 min.
              </small>
            )}
          </div>

          {locationMessage && <p className="status-note">{locationMessage}</p>}
          {weatherQuery.isError && (
            <p className="status-note error-note">
              No se pudo consultar el clima. Revisa internet o intenta actualizar.
            </p>
          )}
          {floodQuery.isError && (
            <p className="status-note error-note">
              No se pudo consultar caudal de rio. La alerta queda solo con lluvia.
            </p>
          )}
        </aside>
      </main>

      <section className="response-grid">
        <div className="timeline-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">Pronostico por hora</span>
              <h2 className="visually-hidden">Pronostico por hora</h2>
            </div>
            <div className="forecast-chip">
              <Umbrella size={16} aria-hidden="true" />
              Lluvia + riesgo
            </div>
          </div>

          <p className="timeline-note">
            En tormentas, la lluvia puede adelantarse o retrasarse 30-60 min.
            Toma cada hora como una ventana probable, no como un minuto exacto.
          </p>

          <div className="hourly-table" aria-label="Pronostico de 24 horas">
            {nextHours.length > 0 ? (
              nextHours.map((hour) => {
                const hourRisk = getHourRisk(hour)

                return (
                  <article className={`hour-card ${hourRisk.tone}`} key={hour.time}>
                    <div className="hour-time">
                      <strong>{formatTime(hour.time)}</strong>
                      <span>{formatDayLabel(hour.time)}</span>
                    </div>

                    <div className="hour-condition">
                      <span className="weather-pill">
                        {getWeatherIcon(hour.weatherCode, hour.time)}
                      </span>
                      <div>
                        <strong>{describeWeatherCode(hour.weatherCode)}</strong>
                        <span>{describeRain(hour.rain)}</span>
                      </div>
                    </div>

                    <div className="hour-temp">
                      <ThermometerSun size={17} aria-hidden="true" />
                      <div>
                        <strong>{formatTemperature(hour.temperature)}</strong>
                        <span>
                          Sens.{' '}
                          {formatTemperature(
                            hour.apparentTemperature ?? hour.temperature,
                          )}
                        </span>
                      </div>
                    </div>

                    <div className="hour-rain">
                      <div className="rain-line">
                        <div className="rain-bar">
                          <i style={{ width: `${getRainBarWidth(hour)}%` }} />
                        </div>
                        <strong>{formatNumber(hour.rain)} mm</strong>
                      </div>
                      <span>{hour.probability}% probabilidad</span>
                    </div>

                    <div className="hour-wind">
                      <Wind size={17} aria-hidden="true" />
                      <span>
                        {formatDirection(hour.windDirection)}{' '}
                        {hour.windSpeed === undefined
                          ? 'sin dato'
                          : `${formatNumber(hour.windSpeed, 0)} km/h`}
                      </span>
                    </div>

                    <div className={`hour-risk ${hourRisk.tone}`}>
                      <strong>{hourRisk.label}</strong>
                      <span>{hourRisk.advice}</span>
                    </div>
                  </article>
                )
              })
            ) : (
              <p className="empty-state">El pronostico aparecera al cargar datos.</p>
            )}
          </div>
        </div>

        <div className="response-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">Plan inmediato</span>
              <h2>Que hacer</h2>
            </div>
          </div>

          <ol className="action-list">
            <li>{risk.exitAdvice}</li>
            <li>Evita pasos a desnivel, arroyos, canales y calles bajas.</li>
            <li>Actualiza tu ubicacion antes de decidir salir.</li>
            <li>
              Si el riesgo sube, revisa los puntos de apoyo cercanos y espera
              indicaciones oficiales.
            </li>
          </ol>
        </div>
      </section>

      <section className="safety-grid" aria-label="Funciones de emergencia">
        <article className="safety-panel">
          <div className="safety-heading">
            <Bell size={20} aria-hidden="true" />
            <div>
              <span className="section-kicker">Alertas</span>
              <h2>Sin crear cuenta</h2>
            </div>
          </div>
          <p>
            AquaRisk puede avisar en este dispositivo cuando detecte lluvia fuerte,
            tormenta o caudal elevado. En esta version funciona mientras la app
            esta activa; con Supabase se puede programar en segundo plano sin login.
          </p>
          <button type="button" className="secondary-button" onClick={requestNotifications}>
            Activar alertas preventivas
          </button>
          <small>Estado: {formatNotificationStatus(notificationPermission)}</small>
          {alertMessage && <p className="backend-note">{alertMessage}</p>}
        </article>

        <article className="safety-panel">
          <div className="safety-heading">
            <ShieldAlert size={20} aria-hidden="true" />
            <div>
              <span className="section-kicker">Zonas vulnerables</span>
              <h2>Cerca de ti</h2>
            </div>
          </div>
          {riskZones.length > 0 ? (
            <div className="compact-list">
              {riskZones.map((zone) => (
                <div className={`compact-item ${zone.tone}`} key={zone.id}>
                  <div>
                    <strong>{zone.name}</strong>
                    <span>{zone.detail}</span>
                  </div>
                  <em>{formatDistance(zone.distanceKm)}</em>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-state">
              No hay zonas criticas cercanas con el pronostico actual.
            </p>
          )}
        </article>

        <article className="safety-panel">
          <div className="safety-heading">
            <Route size={20} aria-hidden="true" />
            <div>
              <span className="section-kicker">Ubicaciones seguras</span>
              <h2>Puntos de apoyo</h2>
            </div>
          </div>
          {isSafePlacesLoading && (
            <p className="empty-state">Buscando puntos cercanos en Supabase y OpenStreetMap.</p>
          )}
          {hasSafePlacesError && (
            <p className="empty-state">
              No se pudieron consultar puntos seguros por ahora.
            </p>
          )}
          {!isSafePlacesLoading && !hasSafePlacesError && (
            safePlaces.length > 0 ? (
              <div className="compact-list">
                {safePlaces.map((place) => (
                  <div className="compact-item support" key={place.id}>
                    <div>
                      <strong>{place.name}</strong>
                      <span>{place.kind} | {place.source}</span>
                    </div>
                    <em>{formatDistance(place.distanceKm)}</em>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-state">
                No se encontraron puntos de apoyo cercanos en Supabase ni OpenStreetMap.
              </p>
            )
          )}
        </article>
      </section>
    </div>
  )
}

export default App
