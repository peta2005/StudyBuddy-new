export interface AuthUser {
  id: string;
  email: string;
  email_verified: boolean;
  oauth_provider?: string | null;
  created_at: string;
}

export interface AuthSession {
  access_token: string;
  refresh_token: string;
  user: AuthUser;
}

export interface AuthResult {
  error: string | null;
  info?: string | null;
  emailVerificationRequired?: boolean;
}
