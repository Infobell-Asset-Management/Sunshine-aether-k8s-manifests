import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Storage, Timeline, Assessment, Speed } from '@mui/icons-material';
import { List, ListItem, ListItemText, Chip, Divider } from '@mui/material';
import axios from 'axios';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [events, setEvents] = useState([]);
  const [sysMetrics, setSysMetrics] = useState(null);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [s, e, m] = await Promise.all([
          axios.get('/api/stats'),
          axios.get('/api/events'),
          axios.get('/api/system/metrics').catch(() => ({ data: { available: false } })),
        ]);
        setStats(s.data);
        setEvents((e.data || []).slice(0, 5));
        setSysMetrics(m.data || null);
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error('Error fetching dashboard:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, []);

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

  const statCards = [
    {
      title: 'Total Assets',
      value: stats?.total_assets || 0,
      icon: <Storage color="primary" />,
      color: '#1976d2',
    },
    {
      title: 'Events Processed',
      value: stats?.total_events_processed || 0,
      icon: <Timeline color="secondary" />,
      color: '#dc004e',
    },
    {
      title: 'Active Assets',
      value: stats?.active_assets || 0,
      icon: <Speed color="success" />,
      color: '#2e7d32',
    },
    {
      title: 'System Health',
      value: 'Healthy',
      icon: <Assessment color="info" />,
      color: '#0288d1',
    },
  ];

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {statCards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {card.title}
                    </Typography>
                    <Typography variant="h4" component="div">
                      {card.value}
                    </Typography>
                  </Box>
                  <Box sx={{ color: card.color }}>
                    {card.icon}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {sysMetrics?.available && (
        <Box mt={4}>
          <Typography variant="h5" gutterBottom>Host Health</Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1">OS / Kernel</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {sysMetrics.summary.os_kernel || '-'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1">Uptime</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {sysMetrics.summary.uptime || '-'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1">Load Average</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {sysMetrics.summary.loadavg || '-'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1">Top Processes</Typography>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{sysMetrics.summary.processes_top || '-'}</pre>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1">Disk</Typography>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{sysMetrics.summary.disk || '-'}</pre>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1">Network</Typography>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{sysMetrics.summary.network || '-'}</pre>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      )}

      <Box mt={4}>
        <Typography variant="h5" gutterBottom>
          Recent Activity
        </Typography>
        <Card>
          <CardContent>
            {events.length === 0 ? (
              <Typography variant="body2" color="textSecondary">
                No recent events
              </Typography>
            ) : (
              <List>
                {events.map((ev, idx) => (
                  <React.Fragment key={idx}>
                    <ListItem>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="subtitle1">{ev.event_type === 'system_metrics' ? 'System metrics' : `Asset: ${ev.asset_id}`}</Typography>
                            <Chip label={ev.event_type} size="small" />
                          </Box>
                        }
                        secondary={`Node: ${ev.node_id || '-'} · ${new Date(ev.timestamp).toLocaleString()}`}
                      />
                    </ListItem>
                    {idx < events.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            )}
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

export default Dashboard;

