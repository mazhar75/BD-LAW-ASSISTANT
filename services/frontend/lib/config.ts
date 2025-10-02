export const config = {
  gatewayUrl: process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:8081',
  ragUrl: process.env.NEXT_PUBLIC_RAG_URL || 'http://localhost:8000',
  appName: process.env.NEXT_PUBLIC_APP_NAME || 'BD Law Assistant',
  appVersion: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  enableBengali: process.env.NEXT_PUBLIC_ENABLE_BENGALI === 'true',
  enableVoice: process.env.NEXT_PUBLIC_ENABLE_VOICE === 'true',
  maxFileSize: parseInt(process.env.NEXT_PUBLIC_MAX_FILE_SIZE || '10485760'),
  tokenKeys: {
    access: 'bd_law_access_token',
    refresh: 'bd_law_refresh_token',
    user: 'bd_law_user',
  },
} as const;