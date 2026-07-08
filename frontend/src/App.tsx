import { useState, useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import NotFound from "./pages/NotFound";
import AuthPage from "./pages/AuthPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import VerifyEmailPage from "./pages/VerifyEmailPage";
import OAuthCallbackPage from "./pages/OAuthCallbackPage";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { Plus, Clock, MessageSquarePlus, BookOpen, Trash2, LogOut, Loader2 } from "lucide-react";
import { ChatInterface } from "@/components/ChatInterface";
import { apiFetch } from "@/lib/apiClient";
import { useSettings } from "@/hooks/useSettings";

const queryClient = new QueryClient();

interface Chat {
  id: string;
  title: string;
  messages: any[];
  loaded?: boolean;
}

const makeInitialChat = (): Chat => ({
  id: Date.now().toString(),
  title: "New Chat",
  messages: [],
});

function AuthRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AuthPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/auth/callback" element={<OAuthCallbackPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function StudyBuddyApp() {
  const { user, signOut, accessToken } = useAuth();
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [historyLoading, setHistoryLoading] = useState(true);

  const { settings } = useSettings();
  const baseUrl = settings.backendUrl.replace(/\/$/, "");

  // Load sessions from backend when user logs in
  useEffect(() => {
    if (!user || !accessToken) return;
    setHistoryLoading(true);
    apiFetch(baseUrl, "/history/sessions", accessToken)
      .then((r) => r.json())
      .then((data) => {
        const fresh = makeInitialChat();
        if (data.sessions && data.sessions.length > 0) {
          const loaded: Chat[] = data.sessions.map((s: any) => ({
            id: s.session_id,
            title: s.session_title,
            messages: [],          // loaded lazily when clicked
            loaded: false,
          }));
          setChats([fresh, ...loaded]);
          setCurrentChatId(fresh.id);
        } else {
          setChats([fresh]);
          setCurrentChatId(fresh.id);
        }
      })
      .catch(() => {
        const fresh = makeInitialChat();
        setChats([fresh]);
        setCurrentChatId(fresh.id);
      })
      .finally(() => setHistoryLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  // When switching to a chat that hasn't loaded messages yet, fetch them
  useEffect(() => {
    if (!currentChatId || !accessToken) return;
    const chat = chats.find((c) => c.id === currentChatId);
    if (!chat || chat.loaded || chat.messages.length > 0) return;

    apiFetch(baseUrl, `/history/sessions/${currentChatId}`, accessToken)
      .then((r) => r.json())
      .then((data) => {
        if (data.messages) {
          setChats((prev) =>
            prev.map((c) =>
              c.id === currentChatId
                ? {
                    ...c,
                    loaded: true,
                    messages: data.messages.map((m: any) => ({
                      role: m.role,
                      content: m.content,
                      sources: m.sources || [],
                      timestamp: new Date(m.created_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      }),
                    })),
                  }
                : c
            )
          );
        }
      })
      .catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentChatId]);

  const createNewChat = () => {
    const newChat: Chat = makeInitialChat();
    setChats((prev) => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
    setUploadedFile(null);
  };

  const clearAllHistory = async () => {
    // Delete all sessions from backend
    for (const chat of chats) {
      if (accessToken) {
        apiFetch(baseUrl, `/history/sessions/${chat.id}`, accessToken, { method: "DELETE" }).catch(() => {});
      }
    }
    const fresh = makeInitialChat();
    setChats([fresh]);
    setCurrentChatId(fresh.id);
    setUploadedFile(null);
  };

  const deleteChat = async (id: string) => {
    if (accessToken) {
      apiFetch(baseUrl, `/history/sessions/${id}`, accessToken, { method: "DELETE" }).catch(() => {});
    }
    const filtered = chats.filter((c) => c.id !== id);
    setChats(filtered);
    if (filtered.length) setCurrentChatId(filtered[0].id);
    else createNewChat();
  };

  const updateChatMessages = (id: string, messages: any[]) => {
    setChats((prev) =>
      prev.map((chat) =>
        chat.id === id ? { ...chat, messages: [...messages], loaded: true } : chat
      )
    );
  };

  const renameChat = (id: string, title: string) => {
    setChats((prev) =>
      prev.map((chat) => (chat.id === id ? { ...chat, title } : chat))
    );
  };

  const currentChat = chats.find((chat) => chat.id === currentChatId);

  if (historyLoading) {
    return (
      <div className="auth-shell">
        <Loader2 size={28} className="auth-spinner" />
      </div>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon">
            <BookOpen size={18} />
          </div>
          <span className="logo-text">Smart Study Buddy</span>
        </div>

        <div className="sidebar-user">
          <span className="sidebar-user-label">Signed in as</span>
          <span className="sidebar-user-email">{user?.email}</span>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-item nav-item--muted">
            <Clock size={16} />
            <span>History</span>
          </div>

          {chats.map((chat) => (
            <div
              key={chat.id}
              onClick={() => setCurrentChatId(chat.id)}
              className={`nav-item nav-item--chat ${currentChatId === chat.id ? "nav-item--active" : ""}`}
            >
              <MessageSquarePlus size={16} />
              <span className="nav-item-label">{chat.title}</span>
              <button
                className="nav-delete-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  deleteChat(chat.id);
                }}
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </nav>

        <button className="sidebar-logout-btn" onClick={() => signOut()}>
          <LogOut size={15} />
          Sign out
        </button>

        <button className="new-chat-btn" onClick={createNewChat}>
          <Plus size={16} />
          New Chat
        </button>
      </aside>

      <main className="main-area">
        <Routes>
          <Route
            path="/"
            element={
              <ChatInterface
                chat={currentChat}
                uploadedFile={uploadedFile}
                onFileUploaded={(file) => {
                  setUploadedFile(file);
                  renameChat(currentChatId!, file.name.replace(/\.[^/.]+$/, ""));
                }}
                updateChatMessages={(msgs) =>
                  updateChatMessages(currentChatId!, msgs)
                }
                onClearHistory={clearAllHistory}
              />
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  );
}


function AppRouter() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="auth-shell">
        <Loader2 size={28} className="auth-spinner" />
      </div>
    );
  }

  if (!user) {
    return <AuthRoutes />;
  }

  return <StudyBuddyApp />;
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <BrowserRouter>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <AppRouter />
        </TooltipProvider>
      </BrowserRouter>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
