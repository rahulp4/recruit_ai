// src/hooks/useAuth.ts
// import { useState, useEffect } from 'react';
// import { User } from 'firebase/auth';
// import { auth } from '../App'; // Import the auth instance

// interface AuthContextType {
//   user: User | null;
//   isAuthenticated: boolean | null;
//   isLoadingAuth: boolean;
// }

// export const useAuth = (): AuthContextType => {
//   const [user, setUser] = useState<User | null>(null);
//   const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null); // null means checking
//   const [isLoadingAuth, setIsLoadingAuth] = useState<boolean>(true);

//   useEffect(() => {
//     const unsubscribe = auth.onAuthStateChanged((firebaseUser) => {
//       setUser(firebaseUser);
//       setIsAuthenticated(!!firebaseUser); // Convert User object to boolean
//       setIsLoadingAuth(false);
//     });

//     return () => unsubscribe();
//   }, []);

//   return { user, isAuthenticated, isLoadingAuth };
// };

// src/hooks/useAuth.ts
// src/hooks/useAuth.tsx
import React, { useState, useEffect, useContext, createContext, ReactNode } from 'react';
import { User, signOut, onAuthStateChanged } from 'firebase/auth';
import { auth } from '../App';
import { checkAuthStatusApi, loginUserApi } from '../services/apiService';
import axios, { AxiosError } from 'axios';

import { LoginResponseData, BackendMenuItem, AuthUserResponse } from '../types/authTypes';

// Define the shape of the user's application-specific context
interface AppUserContext {
  firebaseUser: User | null;
  isAuthenticated: boolean;
  isLoadingAuth: boolean;
  role: string | null;
  features: Record<string, boolean>; // Still derived from backend, or can be stored
  appUser: AuthUserResponse | null; 
  menuItems: BackendMenuItem[]; 
  logout: () => Promise<void>; 
  setAppUserData: (data: { user: AuthUserResponse; menuItems: BackendMenuItem[]; }) => void;
}

const AuthContext = createContext<AppUserContext | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

// --- LOCAL STORAGE KEYS ---
const LS_MENU_ITEMS_KEY = 'app_menu_items';
const LS_APP_USER_KEY = 'app_user_data';
const LS_USER_ROLE_KEY = 'app_user_role'; // To store simplified role

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [firebaseUser, setFirebaseUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoadingAuth, setIsLoadingAuth] = useState<boolean>(true);
  const [role, setRole] = useState<string | null>(null);
  const [features, setFeatures] = useState<Record<string, boolean>>({});
  const [appUser, setAppUser] = useState<AuthUserResponse | null>(null);
  const [menuItems, setMenuItems] = useState<BackendMenuItem[]>([]);

  const logout = async () => {
    try {
      await signOut(auth);
      // Clear all local state and localStorage
      setFirebaseUser(null);
      setIsAuthenticated(false);
      setRole(null);
      setFeatures({});
      setAppUser(null);
      setMenuItems([]);
      localStorage.removeItem(LS_MENU_ITEMS_KEY);
      localStorage.removeItem(LS_APP_USER_KEY);
      localStorage.removeItem(LS_USER_ROLE_KEY); // Clear role from LS
      // If features were stored in LS, clear them too
    } catch (error) {
      console.error("Error during logout:", error);
    }
  };

  // Function called after successful login (from LoginPage)
  const setAppUserData = (data: { user: AuthUserResponse; menuItems: BackendMenuItem[]; }) => {

     // >>>>>>> CRITICAL DEBUG LOG HERE <<<<<<<
    console.log("AuthContext: setAppUserData received data.menuItems:", data.menuItems);
    console.log("AuthContext: Type of data.menuItems:", typeof data.menuItems, "Is Array:", Array.isArray(data.menuItems));
    console.log("AuthContext: Length of data.menuItems:", data.menuItems?.length);
    // >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    setAppUser(data.user);
    setMenuItems(data.menuItems);
    const newRole = data.user.roles.length > 0 ? data.user.roles[0] : null;
    setRole(newRole);
    // If backend sent features directly in login response, set them
    // setFeatures(data.organization_features || {}); 
    setIsAuthenticated(true); // Now we are truly authenticated at app level
   // Log the state *after* setMenuItems is called, but before next render cycle
    console.log("AuthContext: State after setMenuItems. Current menuItems state in closure:", menuItems.length, "(this might show old state due to closure)"); // This log might be misleading
    console.log("AuthContext: IsAuthenticated set to TRUE. Menu items state set to (received length):", data.menuItems?.length, "items."); 

    // <<<<< PERSIST TO LOCAL STORAGE >>>>>
    try {
      localStorage.setItem(LS_MENU_ITEMS_KEY, JSON.stringify(data.menuItems));
      localStorage.setItem(LS_APP_USER_KEY, JSON.stringify(data.user));
      if (newRole) {
        localStorage.setItem(LS_USER_ROLE_KEY, newRole);
      }
      
      // If features are static or derived, they don't need to be stored.
      // If features come from login response and are dynamic, store them too.
    } catch (e) {
      console.error("Error saving to localStorage:", e);
    }
    console.log("AuthContext: App user data set and persisted.");
  };


  useEffect(() => {
    setIsLoadingAuth(true);
        console.log("AuthContext: useEffect running (initial or auth state change).");

    const unsubscribe = onAuthStateChanged(auth, async (user) => {
            console.log("AuthContext: onAuthStateChanged fired. Firebase User:", user ? user.uid : "null");

      if (user) {
        setFirebaseUser(user);
        // Attempt to load from localStorage first
        try {
          const storedMenuItems = localStorage.getItem(LS_MENU_ITEMS_KEY);
          const storedAppUser = localStorage.getItem(LS_APP_USER_KEY);
          const storedRole = localStorage.getItem(LS_USER_ROLE_KEY);
          console.log("AuthContext: Hydration Check - Stored MenuItems:", storedMenuItems ? "Found" : "Not Found", "Stored AppUser:", storedAppUser ? "Found" : "Not Found");

          console.log("Auth: Checking LocalStorage for menuItems:", storedMenuItems ? "Found" : "Not Found");
          console.log("Auth: Checking LocalStorage for appUser:", storedAppUser ? "Found" : "Not Found");


          if (storedMenuItems && storedAppUser) {
            const parsedMenuItems: BackendMenuItem[] = JSON.parse(storedMenuItems);
            const parsedAppUser: AuthUserResponse = JSON.parse(storedAppUser);
            
            // Validate stored data (e.g., check if UID matches Firebase UID)
            console.log('Auth: parsedAppUser.uid ',parsedAppUser.uid);
            console.log('Auth: user.uid ',parsedAppUser.uid);
            if (parsedAppUser.uid === user.uid) {
              setAppUser(parsedAppUser);
              setMenuItems(parsedMenuItems);
              setRole(storedRole);
              // setFeatures from localStorage if stored
              setIsAuthenticated(true); // Frontend is authenticated based on stored data
              console.log("AuthContext: Hydrated from localStorage. User:", parsedAppUser.email);
              // Now, make a quick backend call to verify session token (HttpOnly)
              // This confirms session is still valid, but doesn't re-fetch menuItems.
              try {
                const response = await checkAuthStatusApi(); // This sends HttpOnly cookie
                if (response.status >= 200 && response.status < 300) {
                  console.log("AuthContext: Backend session token verified.");
                  console.log("AuthContext: Backend session token verified successfully.");

                  // Optional: if backend checkAuthStatusApi returns updated role, update here
                  // const backendStatusData: LoginResponseData = response.data; // Type if /status returns more
                  // setRole(backendStatusData.user_role || storedRole);
                } else {
                  console.log("AuthContext: Backend session token invalid, clearing localStorage.");
                  await logout(); // Logout to clear all state
                }
              } catch (error) {
                console.error("AuthContext: Error verifying backend session token:", error);
                await logout(); // Logout if backend verification fails (network, 401, etc.)
              }
              setIsLoadingAuth(false);
              return; // Exit as we've handled authentication via localStorage and backend check
            } else {
              console.warn("AuthContext: UID mismatch in localStorage, forcing re-authentication.");
              await logout(); // Mismatch implies invalid session, force clean logout
            }
          }
        } catch (e) {
          console.error("Error parsing localStorage data:", e);
          localStorage.clear(); // Clear potentially corrupted storage
          await logout(); // Force logout
        }
        
        // If localStorage was empty, corrupted, or mismatched, fall back to unauthenticated path
        // This will often lead to a redirect to /login
        setIsAuthenticated(false);
        setAppUser(null);
        setMenuItems([]);
        setRole(null);
        console.log("AuthContext: No valid session in localStorage. Initializing unauthenticated.");
        setIsLoadingAuth(false);
        // Optional: If Firebase user exists but no local session, sign them out of Firebase to
        // force a clean login through your app's flow.
        if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
            console.log("AuthContext: Forcing Firebase sign out due to missing app session indicator.");
            await signOut(auth);
        }

      } else {
        // No Firebase user. Clear all local state and localStorage.
        setFirebaseUser(null);
        setIsAuthenticated(false);
        setAppUser(null);
        setMenuItems([]);
        setRole(null);
        localStorage.clear(); // Ensure localStorage is also cleared on Firebase sign out
        console.log("AuthContext: No Firebase user. App not authenticated. LocalStorage cleared.");
        setIsLoadingAuth(false);
      }
    });

    return () => unsubscribe();
  }, []); 

  const contextValue: AppUserContext = {
    firebaseUser,
    isAuthenticated,
    isLoadingAuth,
    role,
    features,
    appUser,
    menuItems,
    logout,
    setAppUserData,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};