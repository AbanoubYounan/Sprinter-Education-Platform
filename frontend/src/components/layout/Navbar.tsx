import { useState } from "react";
import { AppBar, Toolbar, Typography, Button, Avatar, Menu, MenuItem, IconButton, Box, Modal } from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import { useRouter } from "next/router";

const Navbar = () => {
  const router = useRouter();
  const [user, setUser] = useState(null); // Simulate user state (replace with auth logic)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [openModal, setOpenModal] = useState(false);
  const [modalType, setModalType] = useState<"login" | "signup">("login");

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleOpenModal = (type: "login" | "signup") => {
    setModalType(type);
    setOpenModal(true);
  };

  const handleCloseModal = () => {
    setOpenModal(false);
  };

  return (
    <>
      <AppBar position="static" color="primary" className="tw-bg-blue-25 tw-fixed tw-top-0 tw-z-50 tw-max-h-20 tw-w-full">
        <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
          {/* Left Side - Logo & Name */}
          <Box display="flex" alignItems="center">
            <IconButton edge="start" color="inherit" aria-label="menu">
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" sx={{ ml: 2 }}>
              EduPlatform
            </Typography>
          </Box>

          {/* Right Side - User or Login/Signup */}
          {user ? (
            <Box display="flex" alignItems="center">
              <Avatar
                sx={{ cursor: "pointer" }}
                onClick={handleMenuOpen}
              >
                U
              </Avatar>
              <Typography variant="body1" sx={{ ml: 1, cursor: "pointer" }} onClick={handleMenuOpen}>
                John Doe
              </Typography>

              {/* Dropdown Menu */}
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
              >
                <MenuItem onClick={() => router.push("/enrolled")}>My Programs</MenuItem>
                <MenuItem onClick={() => setUser(null)}>Log Out</MenuItem>
              </Menu>
            </Box>
          ) : (
            <Box>
              <Button color="inherit" onClick={() => handleOpenModal("login")}>
                Login
              </Button>
              <Button color="secondary" variant="contained" onClick={() => handleOpenModal("signup")} sx={{ ml: 1 }}>
                Sign Up
              </Button>
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {/* Login/Signup Modal */}
      <Modal open={openModal} onClose={handleCloseModal}>
        <Box sx={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: 400,
          bgcolor: "background.paper",
          boxShadow: 24,
          p: 4,
          borderRadius: 2,
        }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            {modalType === "login" ? "Login" : "Sign Up"}
          </Typography>
          <Typography variant="body2">
            {/* Here you can add a login/signup form */}
            {modalType === "login" ? "Login Form Goes Here" : "Sign Up Form Goes Here"}
          </Typography>
          <Button variant="contained" color="primary" fullWidth sx={{ mt: 2 }} onClick={handleCloseModal}>
            Close
          </Button>
        </Box>
      </Modal>
    </>
  );
};

export default Navbar;
