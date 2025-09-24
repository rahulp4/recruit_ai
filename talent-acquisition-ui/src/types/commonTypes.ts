// src/types/commonTypes.ts
export interface BackendErrorResponse { // <<<<<< ADD 'export' HERE
  message?: string;
  error?: string;
  // Add other common error fields if your backend sends them consistently in error payloads
}

export {}; // <<<<< ADD THIS LINE TO MAKE IT A MODULE