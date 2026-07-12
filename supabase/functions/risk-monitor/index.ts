import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

type AlertTarget = {
  id: string
  latitude: number
  longitude: number
  min_score: number
  source: 'monitored' | 'subscription'
}

type WeatherResponse = {
  current?: {
    precipitation?: number
    weather_code?: number
  }
  hourly?: {
    precipitation?: number[]
    precipitation_probability?: number[]
    weather_code?: number[]
  }
}

const thunderCodes = new Set([95, 96, 99])

function classifyRain(mmPerHour: number) {
  if (mmPerHour < 0.2) return 'sin lluvia'
  if (mmPerHour < 2.5) return 'lluvia ligera'
  if (mmPerHour < 7.5) return 'lluvia moderada'
  if (mmPerHour < 15) return 'lluvia fuerte'
  return 'lluvia muy fuerte'
}

function classifyRisk(score: number, thunderLikely: boolean) {
  if (thunderLikely || score >= 78) return 'critico'
  if (score >= 58) return 'alto'
  if (score >= 32) return 'medio'
  return 'bajo'
}

async function fetchWeather(latitude: number, longitude: number) {
  const params = new URLSearchParams({
    latitude: String(latitude),
    longitude: String(longitude),
    current: 'precipitation,weather_code',
    hourly: 'precipitation,precipitation_probability,weather_code',
    forecast_days: '1',
    timezone: 'auto',
  })

  const response = await fetch(`https://api.open-meteo.com/v1/forecast?${params}`)
  if (!response.ok) throw new Error('Open-Meteo request failed')
  return response.json() as Promise<WeatherResponse>
}

Deno.serve(async () => {
  const supabaseUrl = Deno.env.get('SUPABASE_URL')
  const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')

  if (!supabaseUrl || !serviceRoleKey) {
    return new Response('Missing Supabase env vars', { status: 500 })
  }

  const supabase = createClient(supabaseUrl, serviceRoleKey)

  const { data: monitoredLocations, error: monitoredError } = await supabase
    .from('monitored_location_points')
    .select('id, latitude, longitude')
    .eq('is_active', true)

  const { data: alertSubscriptions, error: subscriptionError } = await supabase
    .from('alert_subscription_points')
    .select('id, latitude, longitude, min_score')
    .eq('is_active', true)

  if (monitoredError && subscriptionError) {
    return Response.json(
      { error: `${monitoredError.message}; ${subscriptionError.message}` },
      { status: 500 },
    )
  }

  const targets: AlertTarget[] = [
    ...((monitoredLocations ?? []) as Array<Omit<AlertTarget, 'min_score' | 'source'>>).map(
      (location) => ({
        ...location,
        min_score: 58,
        source: 'monitored' as const,
      }),
    ),
    ...((alertSubscriptions ?? []) as Array<Omit<AlertTarget, 'source'>>).map(
      (subscription) => ({
        ...subscription,
        source: 'subscription' as const,
      }),
    ),
  ]

  const processed = []

  for (const location of targets) {
    const weather = await fetchWeather(location.latitude, location.longitude)
    const hourlyRain = weather.hourly?.precipitation?.slice(0, 6) ?? []
    const probability = weather.hourly?.precipitation_probability?.slice(0, 6) ?? []
    const codes = weather.hourly?.weather_code?.slice(0, 12) ?? []
    const rainNow = weather.current?.precipitation ?? 0
    const rainNext6h = hourlyRain.reduce((total, value) => total + value, 0)
    const maxProbability = Math.max(...probability, 0)
    const thunderLikely = codes.some((code) => thunderCodes.has(code))
    const score = Math.min(
      100,
      Math.round(rainNow * 12 + rainNext6h * 4 + maxProbability * 0.35 + (thunderLikely ? 22 : 0)),
    )
    const riskLevel = classifyRisk(score, thunderLikely)
    const rainLabel = classifyRain(Math.max(rainNow, rainNext6h / 6))

    const { data: snapshot } = await supabase
      .from('weather_snapshots')
      .insert({
        point: `SRID=4326;POINT(${location.longitude} ${location.latitude})`,
        rain_now_mm: rainNow,
        rain_next_6h_mm: rainNext6h,
        probability_max: maxProbability,
        weather_code: weather.current?.weather_code,
        thunder_likely: thunderLikely,
      })
      .select('id')
      .single()

    const recommendation =
      riskLevel === 'critico' || riskLevel === 'alto'
        ? 'Evita salir si no es necesario y revisa rutas seguras.'
        : 'Puedes salir con precaucion y seguir monitoreando.'

    const { data: assessment } = location.source === 'monitored'
      ? await supabase
        .from('risk_assessments')
        .insert({
          monitored_location_id: location.id,
          weather_snapshot_id: snapshot?.id,
          risk_level: riskLevel,
          score,
          rain_label: rainLabel,
          recommendation,
        })
        .select('id')
        .single()
      : { data: null }

    if (score >= location.min_score) {
      await supabase.from('alerts').insert({
        monitored_location_id: location.source === 'monitored' ? location.id : null,
        alert_subscription_id:
          location.source === 'subscription' ? location.id : null,
        risk_assessment_id: assessment?.id ?? null,
        title: `AquaRisk: riesgo ${riskLevel}`,
        body: recommendation,
        severity: riskLevel === 'bajo' ? 'info' : riskLevel,
        sent_at: new Date().toISOString(),
      })
    }

    processed.push({
      location_id: location.id,
      source: location.source,
      risk_level: riskLevel,
      score,
    })
  }

  return Response.json({ processed })
})
