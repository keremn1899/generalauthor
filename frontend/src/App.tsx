import { WorldPage } from "./world/WorldPage";
import { IconPreview } from "./world/IconPreview";

export default function App() {
  return window.location.pathname === "/icon-preview" ? <IconPreview /> : <WorldPage />;
}
