import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { Assessment, Storage, Timeline, Dashboard } from '@mui/icons-material';

const Header = () => {
  const navItems = [
    { text: 'Dashboard', path: '/', icon: <Dashboard /> },
    { text: 'Assets', path: '/assets', icon: <Storage /> },
    { text: 'Events', path: '/events', icon: <Timeline /> },
    { text: 'Stats', path: '/stats', icon: <Assessment /> },
  ];

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          AssetTrack
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {navItems.map((item) => (
            <Button
              key={item.text}
              color="inherit"
              component={RouterLink}
              to={item.path}
              startIcon={item.icon}
            >
              {item.text}
            </Button>
          ))}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;

