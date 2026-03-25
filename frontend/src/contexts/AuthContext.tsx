import React, { createContext, useContext, useState, useEffect } from 'react'
import { auth } from '../api'
import type { User } from '../types'

interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  register: (username: string, email: string, password: string) => Promise<void>
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const storedToken = localStorage.getItem('token')
    const storedUsername = localStorage.getItem('username')
    if (storedToken && storedUsername) {
      setToken(storedToken)
      setUser({ id: 0, username: storedUsername, email: '' })
    }
    setIsLoading(false)
  }, [])

  const login = async (username: string, password: string) => {
    const data = await auth.login(username, password)
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('username', username)
    setToken(data.access_token)
    setUser({ id: 0, username, email: '' })
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    setToken(null)
    setUser(null)
  }

  const register = async (username: string, email: string, password: string) => {
    await auth.register(username, email, password)
    await login(username, password)
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, register, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
