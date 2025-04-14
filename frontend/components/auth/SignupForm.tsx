import {
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  TextField,
  Typography,
  Alert,
} from '@mui/material';
import { useState } from 'react';
import axios from 'axios';
const ENV_MODE = process.env.NEXT_PUBLIC_ENV_MODE
const DEV_DOMAIN_NAME = process.env.NEXT_PUBLIC_DEV_DOMAIN_NAME
const PRO_DOMAIN_NAME = process.env.NEXT_PUBLIC_PRO_DOMAIN_NAME

export default function SignupForm({ onSwitch }: { onSwitch: (mode: 'login') => void }) {
  const [form, setForm] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    agree: true,
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setForm({ ...form, [name]: type === 'checkbox' ? checked : value });
  };

  const handleSubmit = async () => {
    setMessage(null);

    if (!form.fullName || !form.email || !form.password || !form.confirmPassword) {
      return setMessage({ type: 'error', text: 'All fields are required.' });
    }

    if (form.password !== form.confirmPassword) {
      return setMessage({ type: 'error', text: 'Passwords do not match.' });
    }

    if (!form.agree) {
      return setMessage({ type: 'error', text: 'You must agree to the terms and conditions.' });
    }

    try {
      setLoading(true);
      const res = await axios.post(`${ENV_MODE=='DEV'?DEV_DOMAIN_NAME:PRO_DOMAIN_NAME}api/auth/sign-up`, {
        FullName: form.fullName,
        Email: form.email,
        Password: form.password,
      });

      setMessage({ type: 'success', text: res.data.message || 'Signup successful!' });
    } catch (err: any) {
      const errMsg = err?.response?.data?.Message || err?.response?.data?.message || 'Signup failed';
      setMessage({ type: 'error', text: errMsg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <TextField
        fullWidth
        label="Full Name"
        variant="outlined"
        margin="normal"
        name="fullName"
        value={form.fullName}
        onChange={handleChange}
      />

      <TextField
        fullWidth
        label="Email"
        variant="outlined"
        margin="normal"
        name="email"
        value={form.email}
        onChange={handleChange}
      />

      <TextField
        fullWidth
        label="Password"
        variant="outlined"
        margin="normal"
        name="password"
        type="password"
        value={form.password}
        onChange={handleChange}
      />

      <TextField
        fullWidth
        label="Confirm Password"
        variant="outlined"
        margin="normal"
        name="confirmPassword"
        type="password"
        value={form.confirmPassword}
        onChange={handleChange}
      />

      <FormControlLabel
        control={
          <Checkbox
            name="agree"
            checked={form.agree}
            onChange={handleChange}
          />
        }
        label={
          <Typography fontSize="small">
            I agree to the <span className="text-gray-700 font-medium underline">terms and conditions</span>
          </Typography>
        }
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
        onClick={handleSubmit}
        disabled={loading}
      >
        {loading ? 'Signing up...' : 'Join Us'}
      </Button>

      <Typography align="center" mt={2} fontSize="small">
        Already have an account?{' '}
        <span className="text-blue-600 cursor-pointer" onClick={() => onSwitch('login')}>
          Login
        </span>
      </Typography>
    </Box>
  );
}