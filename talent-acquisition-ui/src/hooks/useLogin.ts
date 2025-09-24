// src/hooks/useLogin.ts
import { useState, FormEvent } from 'react';
import { signInWithEmailAndPassword } from 'firebase/auth';
import { auth } from '../App';
import { loginUserApi } from '../services/apiService';
import axios, { AxiosError } from 'axios';
import { LoginResponseData } from '../types/authTypes';

interface UseLoginResult {
  organizationId: string;
  setOrganizationId: (id: string) => void;
  email: string;
  setEmail: (email: string) => void;
  password: string;
  setPassword: (password: string) => void;
  errorMessage: string;
  isLoading: boolean;
  handleLogin: (event: FormEvent) => Promise<LoginResponseData | null>; // This is correct
}

const useLogin = (): UseLoginResult => {
  const [organizationId, setOrganizationId] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleLogin = async (e: FormEvent): Promise<LoginResponseData | null> => { // Correct
    e.preventDefault();
    setErrorMessage('');
    setIsLoading(true);

    if (!organizationId || !email || !password) {
      setErrorMessage('All fields are required.');
      setIsLoading(false);
      return null;
    }

    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const firebaseIdToken = await userCredential.user.getIdToken();
      
      console.log("Successfully authenticated with Firebase. User UID:", userCredential.user.uid);

      const backendResponse = await loginUserApi(organizationId, firebaseIdToken); 
      const result: LoginResponseData = backendResponse.data; // <<<<<< Get the actual data
      
      console.log("Backend login successful via Axios:", result.message);
      // alert('Login successful!'); // REMOVE THIS LINE (Causes warning)
      return result; // <<<<<< Return the actual data
    } catch (error: any) {
      console.error("Authentication Error (Firebase or Backend/Axios):", error);
      if (axios.isAxiosError(error)) { 
        const axiosError = error as AxiosError<any>;
        if (axiosError.response) {
          const errorData = axiosError.response.data;
          setErrorMessage(errorData?.message || axiosError.message || 'Login failed from backend.');
        } else if (axiosError.request) {
          setErrorMessage('No response from authentication service. Check network.');
        } else {
          setErrorMessage('Error during login request setup: ' + axiosError.message);
        }
      } else if (error.code) { // Firebase errors
        switch (error.code) {
          case 'auth/invalid-email': setErrorMessage('Invalid email address format.'); break;
          case 'auth/user-disabled': setErrorMessage('Your account has been disabled.'); break;
          case 'auth/user-not-found':
          case 'auth/wrong-password':
          case 'auth/invalid-credential': setErrorMessage('Invalid email or password.'); break;
          case 'auth/too-many-requests': setErrorMessage('Too many login attempts. Please try again later.'); break;
          default: setErrorMessage(error.message || 'An unexpected Firebase error occurred.');
        }
      } else {
        setErrorMessage('An unexpected error occurred during login.');
      }
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    organizationId, setOrganizationId, email, setEmail, password, setPassword,
    errorMessage, isLoading, handleLogin,
  };
};

export default useLogin;