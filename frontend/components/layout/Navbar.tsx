'use client';
import { useState } from "react";
import { AppBar, Toolbar, Typography, Button, Avatar, Menu, MenuItem, IconButton, Box } from "@mui/material";
import { useRouter } from 'next/navigation';
import AuthModal from '@/components/auth/AuthModal'; // Adjust path as needed


const Navbar = () => {
  const router = useRouter();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [mode, setMode] = useState<'login' | 'signup' | 'forgot'>('login');

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const isLoggedIn = false

  return (
    <AppBar position="static" color="default" className="bg-gray-100 fixed top-0 z-50 w-full shadow-sm">
      <Toolbar sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        {/* Left Side - Logo */}
        <Box display="flex" alignItems="center" className="block">
          <img src="https://sprintscdn.azureedge.net/production/files/174321119867e74abe1c45d.svg" alt="Logo" style={{ width: "120px", height: "32px" }} />
        </Box>

        {/* Center - Navigation Links */}
        <Box className="hidden md:flex" gap={3}  sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Typography variant="body1" className="cursor-pointer text-gray-700 hover:text-black">
            Learning
          </Typography>
          <Typography variant="body1" className="cursor-pointer text-gray-700 hover:text-black">
            Hire Our Graduates
          </Typography>
        </Box>

        {/* Right Side - Language, Cart, Profile */}
        <Box display="flex" alignItems="center" gap={2}>
          {isLoggedIn ? (
            <>
              {/* User Profile */}
              <Box display="flex" alignItems="center" className="cursor-pointer" onClick={handleMenuOpen}>
                {/* <Avatar src="/profile.jpg" alt="Profile" className="tw-w-8 tw-h-8" /> */}
                <Typography variant="body1" className="ml-1">Abanoub</Typography>
              </Box>

              {/* Dropdown Menu */}
              <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
                <MenuItem onClick={() => { router.push("/profile"); handleMenuClose(); }}>Profile</MenuItem>
                <MenuItem onClick={() => { router.push("/logout"); handleMenuClose(); }}>Log Out</MenuItem>
              </Menu>
            </>
          ) : (
            <>
              <Button variant="outlined" onClick={() => { setAuthModalOpen(true); setMode("login")}}>
                Login
              </Button>
              <Button variant="contained" onClick={() => { setAuthModalOpen(true); setMode("signup") }}>
                Sign Up
              </Button>
            </>
          )}
        </Box>
      </Toolbar>
      <AuthModal init_mode={mode} open={authModalOpen} onClose={() => setAuthModalOpen(false)} />
    </AppBar>
  );
};

export default Navbar;
