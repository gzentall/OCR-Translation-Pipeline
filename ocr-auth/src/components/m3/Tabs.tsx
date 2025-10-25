'use client'

import { useEffect, useRef, forwardRef } from 'react'
import '@material/web/tabs/tabs.js'
import '@material/web/tabs/primary-tab.js'

interface Tab {
  label: string
  icon?: string
}

interface TabsProps {
  tabs: Tab[]
  activeTabIndex?: number
  onChange?: (index: number) => void
  className?: string
}

export const Tabs = forwardRef<HTMLElement, TabsProps>(
  ({ tabs, activeTabIndex = 0, onChange, className }, ref) => {
    const tabsRef = useRef<any>(null)

    useEffect(() => {
      if (ref && typeof ref === 'function') {
        ref(tabsRef.current)
      } else if (ref) {
        (ref as any).current = tabsRef.current
      }
    }, [ref])

    useEffect(() => {
      if (tabsRef.current) {
        tabsRef.current.activeTabIndex = activeTabIndex
      }
    }, [activeTabIndex])

    const handleChange = (e: any) => {
      if (onChange) {
        onChange(e.target.activeTabIndex)
      }
    }

    return (
      <md-tabs ref={tabsRef} className={className} onchange={handleChange}>
        {tabs.map((tab, index) => (
          <md-primary-tab key={index} aria-label={tab.label}>
            {tab.icon && <md-icon slot="icon">{tab.icon}</md-icon>}
            {tab.label}
          </md-primary-tab>
        ))}
      </md-tabs>
    )
  }
)

Tabs.displayName = 'Tabs'

