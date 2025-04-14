'use client';
/* eslint-disable  @typescript-eslint/no-explicit-any */
import { useState } from 'react';
import { Box, Button, TextField, Typography, Alert } from '@mui/material';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import { useRouter } from 'next/navigation';
const ENV_MODE = process.env.NEXT_PUBLIC_ENV_MODE
const DEV_DOMAIN_NAME = process.env.NEXT_PUBLIC_DEV_DOMAIN_NAME
const PRO_DOMAIN_NAME = process.env.NEXT_PUBLIC_PRO_DOMAIN_NAME

export default function LoginForm({ onSwitch, setUser, handleClose }: { onSwitch: (mode: 'signup' | 'forgot') => void, setUser: any, handleClose:any}) {
  const router = useRouter();
  const [form, setForm] = useState({ email: '', password: '' });
  const [message, setMessage] = useState<{ text: string; type: 'error' | 'success' } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleLogin = async () => {
    setMessage(null);

    if (!form.email || !form.password) {
      return setMessage({ type: 'error', text: 'Email and Password are required.' });
    }

    try {
      setLoading(true);
      const res = await axios.post(`${ENV_MODE=='DEV'?DEV_DOMAIN_NAME:PRO_DOMAIN_NAME}api/auth/login`, {
        Email: form.email,
        Password: form.password,
      });

      const token = res.data.token;

      // Save token
      
      // Decode and store expiry
      const decoded: any = jwtDecode(token);      
      localStorage.setItem('token', token);
      window.dispatchEvent(new Event('tokenChange'));
      localStorage.setItem('user', decoded);
      setUser(decoded)

      setMessage({ type: 'success', text: 'Login successful! Redirecting...' });
      // window.open(`/courses`);
      router.push('/courses');
      handleClose()
      // Optional: redirect or update global auth state
      // router.push('/dashboard') or setAuth({ user: decoded, token })

    } catch (err: any) {
      const msg =
        err?.response?.data?.Message || err?.response?.data?.message || 'Login failed.';
      setMessage({ type: 'error', text: msg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <TextField
        fullWidth
        label="Email"
        name="email"
        variant="outlined"
        margin="normal"
        value={form.email}
        onChange={handleChange}
      />
      <TextField
        fullWidth
        label="Password"
        name="password"
        variant="outlined"
        type="password"
        margin="normal"
        value={form.password}
        onChange={handleChange}
      />

      {message && (
        <Alert severity={message.type} sx={{ mt: 2 }}>
          {message.text}
        </Alert>
      )}

      <Button
        fullWidth
        variant="contained"
        sx={{ mt: 2, bgcolor: '#0066FF' }}
        onClick={handleLogin}
        disabled={loading}
      >
        {loading ? 'Logging in...' : 'Login'}
      </Button>

      <Typography align="center" mt={2} fontSize="small" className="cursor-pointer" onClick={() => onSwitch('forgot')}>
        Forgot your password?
      </Typography>

      <Typography align="center" mt={1} fontSize="small">
        Don’t have an account?{' '}
        <span className="text-blue-600 cursor-pointer" onClick={() => onSwitch('signup')}>
          Join Us
        </span>
      </Typography>
    </Box>
  );
}