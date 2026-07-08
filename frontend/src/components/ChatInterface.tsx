import { useState, useRef, useEffect } from "react";
import { Send, Paperclip, Settings, Zap, Target, Clock, Lock } from "lucide-react";
import { UploadZone } from "@/components/UploadZone";
import { ChatMessage, TypingMessage, type Message } from "@/components/ChatMessage";
import { GeneralSettings } from "@/components/GeneralSettings";
import { useSettings } from "@/hooks/useSettings";
import { useAuth } from "@/contexts/AuthContext";
import { apiFetch, parseApiError } from "@/lib/apiClient";
import { useToast } from "@/components/ui/use-toast";

interface ChatInterfaceProps {
  chat: any;
  uploadedFile: File | null;
  onFileUploaded: (file: File) => void;
  updateChatMessages: (messages: Message[]) => void;
  onClearHistory?: () => void;
}

function getTime() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export const ChatInterface = ({
  chat,
  uploadedFile,
  onFileUploaded,
  updateChatMessages,
  onClearHistory,
}: ChatInterfaceProps) => {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const { settings, updateSetting, resetSettings } = useSettings();
  const { accessToken } = useAuth();
  const { toast } = useToast();
  const bottomRef = useRef<HTMLDivElement>(null);

  const messages: Message[] = chat?.messages || [];

  useEffect(() => {
    if (settings.autoScroll) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading, settings.autoScroll]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const query = input;
    const userMessage: Message = {
      role: "user",
      content: query,
      timestamp: getTime(),
    };
    const newMessages = [...messages, userMessage];
    updateChatMessages(newMessages);
    setInput("");
    setIsLoading(true);

    const baseUrl = settings.backendUrl.replace(/\/$/, "");

    if (!accessToken) {
      updateChatMessages([
        ...newMessages,
        {
          role: "assistant",
          content: "Your session expired. Please sign in again.",
          timestamp: getTime(),
        },
      ]);
      setIsLoading(false);
      return;
    }

    try {
      const response = await apiFetch(baseUrl, "/ask", accessToken, {
        method: "POST",
        body: JSON.stringify({
          query,
          session_id: chat?.id,
          session_title: chat?.title,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(await parseApiError(response));
      }

      const assistantMessage: Message = {
        role: "assistant",
        content: data.answer || "No response received from backend.",
        sources: data.sources || [],
        timestamp: getTime(),
      };

      updateChatMessages([...newMessages, assistantMessage]);
    } catch (error) {
      const assistantMessage: Message = {
        role: "assistant",
        content:
          error instanceof Error && error.message === "Failed to fetch"
            ? "Backend unreachable. Stop and restart the Flask server, then try again."
            : error instanceof Error
              ? error.message
              : "Server error. Check that the Flask backend is running.",
        timestamp: getTime(),
      };
      updateChatMessages([...newMessages, assistantMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    const formData = new FormData();
    formData.append("pdf", file);
    const baseUrl = settings.backendUrl.replace(/\/$/, "");

    if (!accessToken) {
      toast({
        title: "Session expired",
        description: "Please sign in again to upload documents.",
        variant: "destructive",
      });
      return;
    }

    try {
      const response = await apiFetch(baseUrl, "/upload", accessToken, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        onFileUploaded(file);
        toast({
          title: "Upload successful",
          description: `"${file.name}" is ready for questions.`,
          duration: 3000,
        });
      } else {
        toast({
          title: "Upload failed",
          description: await parseApiError(response),
          variant: "destructive",
        });
      }
    } catch {
      toast({
        title: "Backend unreachable",
        description: "Could not connect to Flask. Restart the backend and try again.",
        variant: "destructive",
      });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (settings.enterToSend && e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="chat-layout">
      <header className="chat-header">
        <div className="chat-header-left">
          <h1 className="chat-title">
            {uploadedFile ? uploadedFile.name.replace(/\.[^/.]+$/, "") : "Smart Study Buddy"}
          </h1>
          <p className="chat-subtitle">
            {uploadedFile ? `${uploadedFile.name}` : "Ready to help you study"}
          </p>
        </div>
        <button
          className="icon-btn"
          title="General settings"
          onClick={() => setSettingsOpen(true)}
        >
          <Settings size={17} />
        </button>
      </header>

      <div className="chat-body">
        {!uploadedFile && !hasMessages ? (
          <div className="welcome-wrap">
            <UploadZone onFileUploaded={handleFileUpload} />

            <div className="feature-grid">
              <div className="feature-card">
                <div className="feature-icon"><Zap size={18} /></div>
                <div>
                  <p className="feature-title">Ask Anything</p>
                  <p className="feature-desc">Get instant answers from your PDF</p>
                </div>
              </div>
              <div className="feature-card">
                <div className="feature-icon"><Target size={18} /></div>
                <div>
                  <p className="feature-title">Accurate &amp; Relevant</p>
                  <p className="feature-desc">AI finds the best answers from your document</p>
                </div>
              </div>
              <div className="feature-card">
                <div className="feature-icon"><Clock size={18} /></div>
                <div>
                  <p className="feature-title">Save Time</p>
                  <p className="feature-desc">Study smarter and faster with AI</p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="messages-wrap">
            {messages.map((msg, i) => (
              <ChatMessage key={i} message={msg} settings={settings} />
            ))}

            {isLoading && <TypingMessage compactMode={settings.compactMode} />}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="chat-input-wrap">
        <div className="chat-input-bar">
          <label className="attach-btn" title="Attach PDF">
            <Paperclip size={18} />
            <input
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFileUpload(f);
              }}
            />
          </label>

          <input
            id="chat-input-field"
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              uploadedFile
                ? "Ask a question about your document..."
                : "Upload a PDF first, or just ask anything..."
            }
            disabled={isLoading}
          />

          <button
            id="send-btn"
            className="send-btn"
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
          >
            <Send size={16} />
          </button>
        </div>

        <p className="privacy-note">
          <Lock size={11} />
          Your documents are stored in your private account workspace.
        </p>
      </div>

      <GeneralSettings
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        settings={settings}
        onUpdate={updateSetting}
        onReset={resetSettings}
        onClearHistory={onClearHistory}
      />
    </div>
  );
};
