import React, { useState, useEffect } from 'react';
import {
  List,
  ListItem,
  ListItemText,
  Paper,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Chip,
  Divider,
  Grid,
} from '@mui/material';
import axios from 'axios';

const Events = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const response = await axios.get('/api/events');
        setEvents(response.data);
      } catch (err) {
        setError('Failed to load events');
        console.error('Error fetching events:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, []);

  const getEventTypeColor = (eventType) => {
    switch (eventType?.toLowerCase()) {
      case 'create':
        return 'success';
      case 'update':
        return 'info';
      case 'delete':
        return 'error';
      case 'maintenance':
        return 'warning';
      case 'system_metrics':
        return 'primary';
      default:
        return 'default';
    }
  };

  const renderSystemMetrics = (event) => {
    const d = event?.data || {};
    return (
      <Box sx={{ mt: 1 }}>
        <Typography variant="subtitle2">Host</Typography>
        <Typography variant="body2" color="textSecondary">
          Node: {event.node_id || '-'} · Time: {new Date(event.timestamp).toLocaleString()}
        </Typography>
        <Box sx={{ mt: 1 }}>
          <Typography variant="subtitle2">CPU / Memory</Typography>
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{d.cpu_mem || '-'}</pre>
        </Box>
        <Box sx={{ mt: 1 }}>
          <Typography variant="subtitle2">Disk</Typography>
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{d.disk || '-'}</pre>
        </Box>
        <Box sx={{ mt: 1 }}>
          <Typography variant="subtitle2">OS / Kernel</Typography>
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{d.os_kernel || '-'}</pre>
          {d.lsb_release && <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{d.lsb_release}</pre>}
        </Box>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2">Users</Typography>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{d.users || '-'}</pre>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2">Top Processes</Typography>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{d.processes_top || '-'}</pre>
          </Grid>
        </Grid>
        <Box sx={{ mt: 1 }}>
          <Typography variant="subtitle2">Network</Typography>
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{d.network || '-'}</pre>
        </Box>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2">Uptime</Typography>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{d.uptime || '-'}</pre>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2">Load Average</Typography>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{d.loadavg || '-'}</pre>
          </Grid>
        </Grid>
      </Box>
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Events
      </Typography>

      <Paper>
        {events.length === 0 ? (
          <Box p={3} textAlign="center">
            <Typography variant="body2" color="textSecondary">
              No events found
            </Typography>
          </Box>
        ) : (
          <List>
            {events.map((event, index) => (
              <React.Fragment key={index}>
                <ListItem>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="subtitle1">
                          {event.event_type === 'system_metrics' ?
                            `System metrics` : `Asset: ${event.asset_id}`}
                        </Typography>
                        <Chip
                          label={event.event_type}
                          color={getEventTypeColor(event.event_type)}
                          size="small"
                        />
                      </Box>
                    }
                    secondary={
                      event.event_type === 'system_metrics'
                        ? renderSystemMetrics(event)
                        : (
                          <Box>
                            <Typography variant="body2" color="textSecondary">
                              Node: {event.node_id}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              Time: {new Date(event.timestamp).toLocaleString()}
                            </Typography>
                            {event.data && Object.keys(event.data).length > 0 && (
                              <Typography variant="body2" color="textSecondary">
                                Data: {JSON.stringify(event.data)}
                              </Typography>
                            )}
                          </Box>
                        )
                    }
                  />
                </ListItem>
                {index < events.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}
      </Paper>
    </Box>
  );
};

export default Events;

