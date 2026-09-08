import { useEffect } from "react";
import { worldIconUrl } from "./worldIcon";

export function useWorldIcon(worldId: string | undefined, mode: "light" | "dark") {
  useEffect(() => {
    const icon = document.createElement("link");
    icon.rel = "icon";
    icon.type = "image/svg+xml";
    icon.href = worldIconUrl(worldId ?? "world", mode);
    document.head.appendChild(icon);
    return () => icon.remove();
  }, [worldId, mode]);
}
