
export interface CreateUserPayload {
  fullName: string;
  email: string;
  organizationId: string;
  role: string;
}

export interface User {
  id: string;
  fullName: string;
  email: string;
  organizationId: string;
  role: string;
  createdAt: string;
}