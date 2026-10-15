import { useEffect, useState } from "react";

/** Tiny hash router (no extra dependency): #/ , #/login , #/register , #/proposal/3 , #/admin */
export function parseHash() {
  const path = window.location.hash.replace(/^#/, "") || "/";
  const parts = path.split("/").filter(Boolean);
  return { path, parts };
}

export function navigate(path) {
  window.location.hash = path;
}

export function useRoute() {
  const [route, setRoute] = useState(parseHash());
  useEffect(() => {
    const onChange = () => setRoute(parseHash());
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}
