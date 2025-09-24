// src/components/auth/RegisterForm.tsx
// import React, { useState } from 'react';
// import { useNavigate } from 'react-router-dom';
// import {
//   Box,
//   Grid,
//   TextField,
//   Button,
//   CircularProgress,
//   Typography,
//   Link
// } from '@mui/material';
// import { Link as RouterLink } from 'react-router-dom';
import { createUserWithEmailAndPassword, sendEmailVerification } from 'firebase/auth';
// import { auth } from '../../App';
// import { registerApi } from '../../services/apiService';
// import StatusAlert, { StatusMessage } from '../common/StatusAlert';
// import axios from 'axios';


// src/components/auth/RegisterForm.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  TextField,
  Button,
  CircularProgress,
  Typography,
  Link
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
// import { createUserWithEmailAndPassword } from 'firebase/auth';
import { auth } from '../../App';
import { registerApi } from '../../services/apiService';
import StatusAlert, { StatusMessage } from '../common/StatusAlert';
import axios from 'axios';

const RegisterForm: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    fullName: '',
    organizationName: '',
    organizationId: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<StatusMessage | null>(null);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;

    if (name === 'organizationId') {
      // Allow only alphanumeric characters and enforce max length
      const alphanumericValue = value.replace(/[^a-zA-Z0-9]/g, '').substring(0, 6);
      setFormData({
        ...formData,
        [name]: alphanumericValue.toLowerCase(),
      });
    } else {
      setFormData({
        ...formData,
        [name]: value,
      });
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setMessage(null);

    if (formData.password !== formData.confirmPassword) {
      setMessage({ type: 'error', text: 'Passwords do not match.' });
      return;
    }

    setLoading(true);

    try {
      // Step 1: Create user in Firebase Auth
      const userCredential = await createUserWithEmailAndPassword(
        auth,
        formData.email,
        formData.password
      );
      const firebaseUser = userCredential.user;
      const firebaseIdToken = await firebaseUser.getIdToken();

        // 2. Send email verification
    await sendEmailVerification(firebaseUser);

      // Step 2: Register user in your backend


        const backendResponse = await registerApi({
        fullName: formData.fullName,
        organizationName: formData.organizationName,
        organizationId: formData.organizationId,
        email: formData.email,
        firebaseIdToken: firebaseIdToken,
      });

      if (backendResponse.status === 201) {
        setMessage({ type: 'success', text: 'Registration successful! Redirecting to login...' });
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      }
    } catch (error: any) {
      let errorMessage = 'An unexpected error occurred. Please try again.';
      if (error.code && error.code.startsWith('auth/')) {
        // Firebase Auth error
        errorMessage = error.message.replace('Firebase: ', '');
      } else if (axios.isAxiosError(error) && error.response) {
        // Backend API error
        const errorData = error.response.data;
        errorMessage = errorData.message || errorData.error || 'Registration failed on our server.';
      }
      setMessage({ type: 'error', text: errorMessage });
      console.error('Registration error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit1 = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setMessage(null);

    if (formData.password !== formData.confirmPassword) {
      setMessage({ type: 'error', text: 'Passwords do not match.' });
      return;
    }
    if (formData.organizationId.length !== 6) {
      setMessage({ type: 'error', text: 'Organization ID must be exactly 5 alphanumeric characters.' });
      return;
    }

    setLoading(true);

    try {
      // Step 1: Create user in Firebase Auth
      const userCredential = await createUserWithEmailAndPassword(
        auth,
        formData.email,
        formData.password
      );
      const firebaseUser = userCredential.user;
      const firebaseIdToken = await firebaseUser.getIdToken();

      // Step 2: Register user in your backend
      const backendResponse = await registerApi({
        fullName: formData.fullName,
        organizationName: formData.organizationName,
        organizationId: formData.organizationId,
        email: formData.email,
        firebaseIdToken: firebaseIdToken,
      });

      if (backendResponse.status === 201) {
        setMessage({ type: 'success', text: 'Registration successful! Redirecting to login...' });
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      }
    } catch (error: any) {
      let errorMessage = 'An unexpected error occurred. Please try again.';
      if (error.code && error.code.startsWith('auth/')) {
        // Firebase Auth error
        errorMessage = error.message.replace('Firebase: ', '');
      } else if (axios.isAxiosError(error) && error.response) {
        // Backend API error
        const errorData = error.response.data;
        errorMessage = errorData.message || errorData.error || 'Registration failed on our server.';
      }
      setMessage({ type: 'error', text: errorMessage });
      console.error('Registration error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography component="h1" variant="h5" align="center">
        Create an Account
      </Typography>
      <StatusAlert message={message} onClose={() => setMessage(null)} />
      <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              required fullWidth id="fullName" label="Full Name" name="fullName"
              autoComplete="name" autoFocus value={formData.fullName} onChange={handleChange}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              required fullWidth id="organizationName" label="Organization Name" name="organizationName"
              autoComplete="organization" value={formData.organizationName} onChange={handleChange}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              required
              fullWidth
              id="organizationId"
              label="Organization ID"
              name="organizationId"
              value={formData.organizationId}
              onChange={handleChange}
              inputProps={{ maxLength: 6, style: { textTransform: 'lowercase' } }}
              helperText="6 alphanumeric characters"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              required fullWidth id="email" label="Email Address" name="email"
              autoComplete="email" type="email" value={formData.email} onChange={handleChange}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              required fullWidth name="password" label="Password" type="password"
              id="password" autoComplete="new-password" value={formData.password} onChange={handleChange}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              required fullWidth name="confirmPassword" label="Confirm Password" type="password"
              id="confirmPassword" autoComplete="new-password" value={formData.confirmPassword} onChange={handleChange}
            />
          </Grid>
        </Grid>
        <Button
          type="submit"
          fullWidth
          variant="contained"
          sx={{ mt: 3, mb: 2 }}
          disabled={loading}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : 'Register'}
        </Button>
        <Grid container justifyContent="flex-end">
          <Grid item>
            <Link component={RouterLink} to="/login" variant="body2">
              Already have an account? Sign in
            </Link>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default RegisterForm;

