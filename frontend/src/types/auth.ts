export type UserRole = "ADMIN" | "OFFICER" | "ANALYST" | "VIEWER";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  department: string;
  designation: string;
  is_active: boolean;
  created_at?: string;
  last_login_at?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface DemoPersona {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
  department: string;
  designation: string;
}
