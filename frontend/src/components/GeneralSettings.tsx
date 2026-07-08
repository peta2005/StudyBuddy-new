import { Settings, RotateCcw, Trash2, Server } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import type { AppSettings } from "@/hooks/useSettings";

interface GeneralSettingsProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  settings: AppSettings;
  onUpdate: <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => void;
  onReset: () => void;
  onClearHistory?: () => void;
}

function SettingRow({
  label,
  description,
  children,
}: {
  label: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="settings-row">
      <div className="settings-row-text">
        <span className="settings-row-label">{label}</span>
        {description && <span className="settings-row-desc">{description}</span>}
      </div>
      {children}
    </div>
  );
}

function NeoToggle({
  checked,
  onChange,
  id,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  id: string;
}) {
  return (
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={checked}
      className={`neo-toggle${checked ? " neo-toggle--on" : ""}`}
      onClick={() => onChange(!checked)}
    >
      <span className="neo-toggle-thumb" />
    </button>
  );
}

export const GeneralSettings = ({
  open,
  onOpenChange,
  settings,
  onUpdate,
  onReset,
  onClearHistory,
}: GeneralSettingsProps) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="settings-dialog">
        <DialogHeader className="settings-dialog-header">
          <div className="settings-dialog-icon">
            <Settings size={18} />
          </div>
          <div>
            <DialogTitle className="settings-dialog-title">General Settings</DialogTitle>
            <DialogDescription className="settings-dialog-desc">
              Configure how Smart Study Buddy behaves on your device.
            </DialogDescription>
          </div>
        </DialogHeader>

        <div className="settings-section">
          <h3 className="settings-section-title">Chat</h3>

          <SettingRow label="Show timestamps" description="Display time on each message">
            <NeoToggle
              id="show-timestamps"
              checked={settings.showTimestamps}
              onChange={(v) => onUpdate("showTimestamps", v)}
            />
          </SettingRow>

          <SettingRow label="Auto-scroll" description="Scroll to newest message automatically">
            <NeoToggle
              id="auto-scroll"
              checked={settings.autoScroll}
              onChange={(v) => onUpdate("autoScroll", v)}
            />
          </SettingRow>

          <SettingRow label="Compact mode" description="Reduce spacing in the chat view">
            <NeoToggle
              id="compact-mode"
              checked={settings.compactMode}
              onChange={(v) => onUpdate("compactMode", v)}
            />
          </SettingRow>

          <SettingRow label="Show sources" description="Display page references on AI answers">
            <NeoToggle
              id="show-sources"
              checked={settings.showSources}
              onChange={(v) => onUpdate("showSources", v)}
            />
          </SettingRow>

          <SettingRow label="Enter to send" description="Press Enter to send a message">
            <NeoToggle
              id="enter-to-send"
              checked={settings.enterToSend}
              onChange={(v) => onUpdate("enterToSend", v)}
            />
          </SettingRow>
        </div>

        <div className="settings-section">
          <h3 className="settings-section-title">
            <Server size={13} />
            Connection
          </h3>

          <div className="settings-field">
            <label htmlFor="backend-url" className="settings-field-label">
              Backend URL
            </label>
            <input
              id="backend-url"
              className="settings-input"
              value={settings.backendUrl}
              onChange={(e) => onUpdate("backendUrl", e.target.value)}
              placeholder="http://127.0.0.1:5000"
            />
          </div>
        </div>

        <div className="settings-section settings-section--actions">
          <button type="button" className="settings-action-btn" onClick={onReset}>
            <RotateCcw size={14} />
            Reset to defaults
          </button>

          {onClearHistory && (
            <button
              type="button"
              className="settings-action-btn settings-action-btn--danger"
              onClick={() => {
                onClearHistory();
                onOpenChange(false);
              }}
            >
              <Trash2 size={14} />
              Clear chat history
            </button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
