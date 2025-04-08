'use client';

import { useAuthModal } from '@/context/AuthModalContext';
import { useState, useEffect } from "react";
import { AppBar, Toolbar, Typography, Button, Avatar, Menu, MenuItem, Box } from "@mui/material";
import { useRouter } from 'next/navigation';
import { jwtDecode } from 'jwt-decode';
import AuthModal from '@/components/auth/AuthModal';

type DecodedUser = {
  Name: string;
  Email: string;
  UserID: string;
  UserType: string;
};

const Navbar = () => {
  const { open, mode, setMode, openModal, closeModal } = useAuthModal();
  const router = useRouter();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  // const [authModalOpen, setAuthModalOpen] = useState(false);
  // const [mode, setMode] = useState<'login' | 'signup' | 'forgot'>('login');
  const [user, setUser] = useState<DecodedUser | null>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  // Load user from localStorage on mount
  useEffect(() => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        const decoded: DecodedUser = jwtDecode(token);
        setUser(decoded);
      }
    } catch (err) {
      console.error("Invalid token");
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setUser(null);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    router.push('/');
  };

  return (
    <AppBar position="static" color="default" className="bg-gray-100 fixed top-0 z-50 w-full shadow-sm">
      <Toolbar sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        {/* Left - Logo */}
        <Box display="flex" alignItems="center">
          <img
            src="/sprints-logo.svg"
            alt="Logo"
            style={{ width: "120px", height: "32px" }}
          />
        </Box>

        {/* Center - Links */}
        <Box className="hidden md:flex" gap={3}>
          <Typography variant="body1" onClick={() => { router.push("/courses");}} className="cursor-pointer text-gray-700 hover:text-black">
            Courses
          </Typography>
          <Typography variant="body1" className="cursor-pointer text-gray-700 hover:text-black">
            Hire Our Graduates
          </Typography>
        </Box>

        {/* Right - Auth Buttons or User */}
        <Box display="flex" alignItems="center" gap={2}>
          {user ? (
            <>
              <Box display="flex" alignItems="center" className="cursor-pointer" onClick={handleMenuOpen}>
                <Avatar>{user.Name?.[0]}</Avatar>
                <Typography variant="body1" className="ml-1">{user.Name}</Typography>
              </Box>

              <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
                <MenuItem onClick={() => { router.push("/profile"); handleMenuClose(); }}>Profile</MenuItem>
                <MenuItem onClick={() => { handleLogout(); handleMenuClose(); }}>Log Out</MenuItem>
              </Menu>
            </>
          ) : (
            <>
              <Button variant="outlined" onClick={() => openModal("login")}>Login</Button>
              <Button variant="contained" onClick={() => openModal("signup")}>Sign Up</Button>
            </>
          )}
        </Box>
      </Toolbar>

      <AuthModal init_mode={mode} open={open} setUser={setUser} onClose={closeModal} />
    </AppBar>
  );
};

export default Navbar;