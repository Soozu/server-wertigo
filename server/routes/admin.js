const express = require('express');
const { PrismaClient } = require('@prisma/client');
const { authenticateToken, requireAdmin } = require('../middleware/auth');

const router = express.Router();
const prisma = new PrismaClient();

// Get dashboard overview analytics
router.get('/analytics/overview', authenticateToken, requireAdmin, async (req, res) => {
  try {
    const { startDate, endDate } = req.query;
    
    // Parse dates or use defaults (last 30 days)
    const end = endDate ? new Date(endDate) : new Date();
    const start = startDate ? new Date(startDate) : new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    
    // Get counts from database
    const [
      totalUsers,
      newUsers,
      totalTrips,
      completedTrips,
      totalTickets
    ] = await Promise.all([
      // Total users
      prisma.user.count(),
      // New users in date range
      prisma.user.count({
        where: {
          createdAt: {
            gte: start,
            lte: end
          }
        }
      }),
      // Total trips
      prisma.trip.count(),
      // Completed trips
      prisma.trip.count({
        where: {
          status: 'completed'
        }
      }),
      // Total tickets
      prisma.generatedTicket.count()
    ]);

    // Calculate stats
    const userGrowthRate = totalUsers > 0 ? (newUsers / totalUsers) * 100 : 0;
    const tripCompletionRate = totalTrips > 0 ? (completedTrips / totalTrips) * 100 : 0;
    
    res.json({
      success: true,
      analytics: {
        totalUsers,
        newUsers,
        userGrowthRate: parseFloat(userGrowthRate.toFixed(2)),
        totalTrips,
        completedTrips,
        tripCompletionRate: parseFloat(tripCompletionRate.toFixed(2)),
        totalTickets,
        period: {
          start: start.toISOString(),
          end: end.toISOString()
        }
      }
    });
  } catch (error) {
    console.error('Analytics overview error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch analytics overview',
      message: 'An error occurred while fetching analytics data'
    });
  }
});

// Get user analytics
router.get('/analytics/users', authenticateToken, requireAdmin, async (req, res) => {
  try {
    const { startDate, endDate } = req.query;
    
    // Parse dates or use defaults (last 30 days)
    const end = endDate ? new Date(endDate) : new Date();
    const start = startDate ? new Date(startDate) : new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    
    // Get user data
    const [
      totalUsers,
      newUsers,
      activeUsers,
      usersByRole
    ] = await Promise.all([
      // Total users
      prisma.user.count(),
      // New users in date range
      prisma.user.count({
        where: {
          createdAt: {
            gte: start,
            lte: end
          }
        }
      }),
      // Active users (users with trips in date range)
      prisma.user.count({
        where: {
          trips: {
            some: {
              createdAt: {
                gte: start,
                lte: end
              }
            }
          }
        }
      }),
      // Users by role
      prisma.user.groupBy({
        by: ['role'],
        _count: {
          id: true
        }
      })
    ]);

    // Transform role data
    const roleDistribution = usersByRole.map(item => ({
      role: item.role,
      count: item._count.id
    }));

    // Calculate growth rate
    const userGrowthRate = totalUsers > 0 ? (newUsers / totalUsers) * 100 : 0;
    
    res.json({
      success: true,
      analytics: {
        totalUsers,
        newUsers,
        activeUsers,
        userGrowthRate: parseFloat(userGrowthRate.toFixed(2)),
        roleDistribution,
        period: {
          start: start.toISOString(),
          end: end.toISOString()
        }
      }
    });
  } catch (error) {
    console.error('User analytics error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch user analytics',
      message: 'An error occurred while fetching user analytics data'
    });
  }
});

// Get trip analytics
router.get('/analytics/trips', authenticateToken, requireAdmin, async (req, res) => {
  try {
    const { startDate, endDate } = req.query;
    
    // Parse dates or use defaults (last 30 days)
    const end = endDate ? new Date(endDate) : new Date();
    const start = startDate ? new Date(startDate) : new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    
    // Get trip data
    const [
      totalTrips,
      newTrips,
      tripsByStatus,
      averageBudget
    ] = await Promise.all([
      // Total trips
      prisma.trip.count(),
      // New trips in date range
      prisma.trip.count({
        where: {
          createdAt: {
            gte: start,
            lte: end
          }
        }
      }),
      // Trips by status
      prisma.trip.groupBy({
        by: ['status'],
        _count: {
          id: true
        }
      }),
      // Average budget
      prisma.trip.aggregate({
        _avg: {
          budget: true
        },
        where: {
          budget: {
            not: null
          }
        }
      })
    ]);

    // Transform status data
    const statusDistribution = tripsByStatus.map(item => ({
      status: item.status,
      count: item._count.id
    }));
    
    res.json({
      success: true,
      analytics: {
        totalTrips,
        newTrips,
        statusDistribution,
        averageBudget: averageBudget._avg.budget ? parseFloat(averageBudget._avg.budget.toFixed(2)) : 0,
        period: {
          start: start.toISOString(),
          end: end.toISOString()
        }
      }
    });
  } catch (error) {
    console.error('Trip analytics error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch trip analytics',
      message: 'An error occurred while fetching trip analytics data'
    });
  }
});

// Get most popular destinations
router.get('/analytics/destinations', authenticateToken, requireAdmin, async (req, res) => {
  try {
    // Get top destinations by count
    const destinations = await prisma.tripDestination.groupBy({
      by: ['city'],
      _count: {
        id: true
      },
      orderBy: {
        _count: {
          id: 'desc'
        }
      },
      take: 10,
      where: {
        city: {
          not: null
        }
      }
    });

    // Transform data
    const popularDestinations = destinations.map(item => ({
      city: item.city,
      count: item._count.id
    }));
    
    res.json({
      success: true,
      destinations: popularDestinations
    });
  } catch (error) {
    console.error('Destinations analytics error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch destinations analytics',
      message: 'An error occurred while fetching destinations data'
    });
  }
});

// Get ticket analytics
router.get('/analytics/tickets', authenticateToken, requireAdmin, async (req, res) => {
  try {
    const { startDate, endDate } = req.query;
    
    // Parse dates or use defaults (last 30 days)
    const end = endDate ? new Date(endDate) : new Date();
    const start = startDate ? new Date(startDate) : new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    
    // Get ticket data
    const [
      totalTickets,
      newTickets,
      ticketsByType,
      usedTickets
    ] = await Promise.all([
      // Total tickets
      prisma.generatedTicket.count(),
      // New tickets in date range
      prisma.generatedTicket.count({
        where: {
          createdAt: {
            gte: start,
            lte: end
          }
        }
      }),
      // Tickets by type
      prisma.generatedTicket.groupBy({
        by: ['ticketType'],
        _count: {
          id: true
        }
      }),
      // Used tickets
      prisma.generatedTicket.count({
        where: {
          isUsed: true
        }
      })
    ]);

    // Transform ticket type data
    const typeDistribution = ticketsByType.map(item => ({
      type: item.ticketType,
      count: item._count.id
    }));

    // Calculate usage rate
    const usageRate = totalTickets > 0 ? (usedTickets / totalTickets) * 100 : 0;
    
    res.json({
      success: true,
      analytics: {
        totalTickets,
        newTickets,
        usedTickets,
        usageRate: parseFloat(usageRate.toFixed(2)),
        typeDistribution,
        period: {
          start: start.toISOString(),
          end: end.toISOString()
        }
      }
    });
  } catch (error) {
    console.error('Ticket analytics error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch ticket analytics',
      message: 'An error occurred while fetching ticket analytics data'
    });
  }
});

// Get system metrics
router.get('/system/metrics', authenticateToken, requireAdmin, async (req, res) => {
  try {
    // Mock system metrics (in a real app, this would come from monitoring tools)
    const systemMetrics = {
      cpuUsage: Math.random() * 40 + 10, // 10-50%
      memoryUsage: Math.random() * 30 + 20, // 20-50%
      diskSpace: {
        total: 100, // GB
        used: Math.random() * 50 + 20, // 20-70 GB
      },
      databaseSize: Math.random() * 2 + 0.5, // 0.5-2.5 GB
      apiLatency: Math.random() * 200 + 50, // 50-250ms
      activeConnections: Math.floor(Math.random() * 100 + 10) // 10-110
    };
    
    res.json({
      success: true,
      metrics: systemMetrics
    });
  } catch (error) {
    console.error('System metrics error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch system metrics',
      message: 'An error occurred while fetching system metrics'
    });
  }
});

module.exports = router; 