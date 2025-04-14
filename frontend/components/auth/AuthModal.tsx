'use client';
/* eslint-disable  @typescript-eslint/no-explicit-any */
import {
  Dialog, DialogTitle, DialogContent, IconButton
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { useEffect, useState } from 'react';
import LoginForm from './LoginForm';
import SignupForm from './SignupForm';
import ForgotPasswordForm from './ForgotPasswordForm';

export default function AuthModal({ init_mode, open, setUser, onClose }: { init_mode: 'login' | 'signup' | 'forgot', open: boolean, setUser: any, onClose: () => void }) {
  const [mode, setMode] = useState<'login' | 'signup' | 'forgot'>('login');

  useEffect(()=>{
    setMode(init_mode)
  },[init_mode])

  const handleClose = () => {
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="xs" fullWidth>
      <DialogTitle>
        {mode === 'login' && 'Log in to your account'}
        {mode === 'signup' && 'Join Us'}
        {mode === 'forgot' && 'Reset Password'}
        <IconButton onClick={handleClose} sx={{ position: 'absolute', top: 8, right: 8 }}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent>
        {mode === 'login' && <LoginForm onSwitch={setMode} handleClose={handleClose} setUser={setUser} />}
        {mode === 'signup' && <SignupForm onSwitch={setMode} />}
        {mode === 'forgot' && <ForgotPasswordForm onSwitch={setMode} />}
      </DialogContent>
    </Dialog>
  );
}
