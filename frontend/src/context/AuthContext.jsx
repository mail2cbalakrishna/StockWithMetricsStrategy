import { createContext } from 'react'

export const AuthContext = createContext({
  keycloak: null,
  authenticated: false,
})
