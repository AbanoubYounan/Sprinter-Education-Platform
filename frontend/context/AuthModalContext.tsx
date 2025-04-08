'use client';
import { createContext, useContext, useState } from 'react';

type Mode = 'login' | 'signup' | 'forgot';

interface AuthModalContextProps {
  open: boolean;
  mode: Mode;
  setMode: (mode: Mode) => void;
  openModal: (mode: Mode) => void;
  closeModal: () => void;
}

const AuthModalContext = createContext<AuthModalContextProps | undefined>(undefined);

export const AuthModalProvider = ({ children }: { children: React.ReactNode }) => {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<Mode>('login');

  const openModal = (newMode: Mode) => {
    setMode(newMode);
    setOpen(true);
  };

  const closeModal = () => setOpen(false);

  return (
    <AuthModalContext.Provider value={{ open, mode, setMode, openModal, closeModal }}>
      {children}
    </AuthModalContext.Provider>
  );
};

export const useAuthModal = () => {
  const context = useContext(AuthModalContext);
  if (!context) throw new Error('useAuthModal must be used within AuthModalProvider');
  return context;
};
