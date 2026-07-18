"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
} from "react";
import { usePathname } from "next/navigation";

interface NavigationLoadingContextType {
  isLoading: boolean;
  progress: number;
  startLoading: () => void;
  stopLoading: () => void;
}

const NavigationLoadingContext = createContext<NavigationLoadingContextType | null>(null);

export function NavigationLoadingProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);

  // Track timers so they can be cleaned up on route transition or component unmount
  const timersRef = useRef<NodeJS.Timeout[]>([]);

  const clearTimers = useCallback(() => {
    timersRef.current.forEach((t) => clearTimeout(t));
    timersRef.current = [];
  }, []);

  const stopLoading = useCallback(() => {
    clearTimers();
    setProgress(100);
    const t = setTimeout(() => {
      setIsLoading(false);
      setProgress(0);
    }, 300);
    timersRef.current.push(t);
  }, [clearTimers]);

  const startLoading = useCallback(() => {
    clearTimers();
    setIsLoading(true);
    setProgress(15);

    // Simulate incremental progress stages to show activity
    const t1 = setTimeout(() => setProgress(45), 150);
    const t2 = setTimeout(() => setProgress(70), 500);
    const t3 = setTimeout(() => setProgress(90), 1000);

    // Safety timeout in case navigation stalls or fails
    const t4 = setTimeout(() => {
      stopLoading();
    }, 8000);

    timersRef.current.push(t1, t2, t3, t4);
  }, [clearTimers, stopLoading]);

  const isInitialMount = useRef(true);

  // Global click listener to intercept internal link clicks and trigger loader instantly
  useEffect(() => {
    const handleAnchorClick = (e: MouseEvent) => {
      // Find the closest anchor tag
      const anchor = (e.target as HTMLElement).closest("a");
      if (!anchor) return;

      const href = anchor.getAttribute("href");
      if (!href) return;

      // Ignore external links, mailto, tel, anchor hashes, target="_blank", or key modifiers
      if (
        href.startsWith("http://") ||
        href.startsWith("https://") ||
        href.startsWith("//") ||
        href.startsWith("mailto:") ||
        href.startsWith("tel:") ||
        href.startsWith("#") ||
        anchor.getAttribute("target") === "_blank" ||
        e.defaultPrevented ||
        e.metaKey ||
        e.ctrlKey ||
        e.shiftKey ||
        e.altKey
      ) {
        return;
      }

      // Check if it's pointing to a different path
      try {
        const targetUrl = new URL(href, window.location.href);
        if (targetUrl.pathname === window.location.pathname) {
          // Ignore if same path and same query parameters
          if (targetUrl.search === window.location.search) {
            return;
          }
        }

        // Trigger transition loading instantly!
        startLoading();
      } catch (err) {
        // Safe check
      }
    };

    document.addEventListener("click", handleAnchorClick, { capture: true });
    return () => {
      document.removeEventListener("click", handleAnchorClick, { capture: true });
    };
  }, [startLoading]);

  // Stop loading automatically when pathname changes (route transition completes)
  // or simulate progress for default Link element navigations
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    if (isLoading) {
      stopLoading();
    } else {
      // Mock progress animation for basic Link/page updates not triggered manually
      clearTimers();
      setIsLoading(true);
      setProgress(15);

      const t1 = setTimeout(() => setProgress(45), 100);
      const t2 = setTimeout(() => setProgress(70), 250);
      const t3 = setTimeout(() => setProgress(100), 500);
      const t4 = setTimeout(() => {
        setIsLoading(false);
        setProgress(0);
      }, 800);

      timersRef.current.push(t1, t2, t3, t4);
    }

    return () => {
      clearTimers();
    };
  }, [pathname]);

  return (
    <NavigationLoadingContext.Provider
      value={{ isLoading, progress, startLoading, stopLoading }}
    >
      {children}
    </NavigationLoadingContext.Provider>
  );
}

export function useNavigationLoading(): NavigationLoadingContextType {
  const context = useContext(NavigationLoadingContext);
  if (!context) {
    throw new Error(
      "useNavigationLoading must be used within a NavigationLoadingProvider"
    );
  }
  return context;
}
