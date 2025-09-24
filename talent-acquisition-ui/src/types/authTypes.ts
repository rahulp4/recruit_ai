// src/types/authTypes.ts

// Interface for each menu item received from the backend
export interface BackendMenuItem {
  displayName: string;
  icon: string; // e.g., "fa-home", "fa-upload"
  id: number;
  name: string;
  orderIndex: number;
  orgId: string | null;
  parentId: number | null;
  path: string;
}

// Interface for the user object within the login response
export interface AuthUserResponse {
  email: string;
  organizationId: string;
  roles: string[]; // e.g., ["Admin"]
  uid: string;
  userId: number;
}

// Interface for the full successful login response payload
export interface LoginResponseData {
  menuItems: BackendMenuItem[];
  message: string;
  user: AuthUserResponse;
}

export interface RegisterPayload {
  fullName: string;
  organizationId: string;
  email: string;
  organizationName: string;
  firebaseIdToken: string;
}