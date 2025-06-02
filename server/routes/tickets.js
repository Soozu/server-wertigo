const express = require('express');
const { body, validationResult } = require('express-validator');
const { PrismaClient } = require('@prisma/client');
const { v4: uuidv4 } = require('uuid');
const { optionalAuth, getSessionId, authenticateToken, requireAdmin } = require('../middleware/auth');

const router = express.Router();
const prisma = new PrismaClient();

// Apply session middleware to all routes
router.use(getSessionId);
router.use(optionalAuth);

// Ticket type configurations
const TICKET_TYPES = {
  FLIGHT: {
    prefix: 'FL',
    length: 6,
    description: 'Flight Ticket'
  },
  BUS: {
    prefix: 'BUS',
    length: 5,
    description: 'Bus Ticket'
  },
  FERRY: {
    prefix: 'FRY',
    length: 5,
    description: 'Ferry Ticket'
  },
  TRAIN: {
    prefix: 'TRN',
    length: 5,
    description: 'Train Ticket'
  },
  HOTEL: {
    prefix: 'HTL',
    length: 6,
    description: 'Hotel Booking'
  },
  TOUR: {
    prefix: 'TUR',
    length: 5,
    description: 'Tour Package'
  },
  BOOKING_REF: {
    prefix: 'BKG',
    length: 8,
    description: 'Booking Reference'
  },
  CONFIRMATION: {
    prefix: 'CNF',
    length: 6,
    description: 'Confirmation Code'
  }
};

// Helper function to generate ticket ID
const generateTicketId = (ticketType, includeTimestamp = true) => {
  const config = TICKET_TYPES[ticketType];
  if (!config) {
    throw new Error('Invalid ticket type');
  }

  const randomPart = Math.random().toString(36).substring(2, 2 + config.length).toUpperCase();
  
  if (includeTimestamp) {
    const timestamp = Date.now().toString().slice(-4); // Last 4 digits of timestamp
    return `${config.prefix}${randomPart}${timestamp}`;
  }
  
  return `${config.prefix}${randomPart}`;
};

// Helper function to check if ticket ID is unique
const ensureUniqueTicketId = async (ticketType, includeTimestamp = true, maxAttempts = 10) => {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const ticketId = generateTicketId(ticketType, includeTimestamp);
    
    const existing = await prisma.generatedTicket.findUnique({
      where: { ticketId }
    });
    
    if (!existing) {
      return ticketId;
    }
  }
  
  throw new Error('Unable to generate unique ticket ID after multiple attempts');
};

// Generate a new ticket
router.post('/generate', [
  body('ticketType')
    .isIn(Object.keys(TICKET_TYPES))
    .withMessage('Invalid ticket type'),
  body('includeTimestamp')
    .optional()
    .isBoolean()
    .withMessage('includeTimestamp must be a boolean'),
  body('metadata')
    .optional()
    .isObject()
    .withMessage('metadata must be an object')
], async (req, res) => {
  try {
    // Check validation errors
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        message: 'Please check your input',
        details: errors.array()
      });
    }

    const { ticketType, includeTimestamp = true, metadata = {} } = req.body;

    // Generate unique ticket ID
    const ticketId = await ensureUniqueTicketId(ticketType, includeTimestamp);

    // Save to database
    const ticket = await prisma.generatedTicket.create({
      data: {
        ticketId,
        ticketType,
        userId: req.user?.id || null,
        sessionId: req.sessionId || null,
        includeTimestamp,
        metadata
      },
      select: {
        id: true,
        ticketId: true,
        ticketType: true,
        isUsed: true,
        includeTimestamp: true,
        metadata: true,
        createdAt: true
      }
    });

    res.status(201).json({
      success: true,
      message: 'Ticket generated successfully',
      ticket: {
        ...ticket,
        description: TICKET_TYPES[ticketType].description
      }
    });

  } catch (error) {
    console.error('Ticket generation error:', error);
    res.status(500).json({
      error: 'Failed to generate ticket',
      message: 'An error occurred while generating the ticket'
    });
  }
});

// Get user's tickets
router.get('/my-tickets', async (req, res) => {
  try {
    const { page = 1, limit = 50, ticketType, isUsed } = req.query;
    const skip = (parseInt(page) - 1) * parseInt(limit);

    // Build where clause
    const where = {};
    
    if (req.user?.id) {
      where.OR = [
        { userId: req.user.id },
        { sessionId: req.sessionId }
      ];
    } else if (req.sessionId) {
      where.sessionId = req.sessionId;
    } else {
      return res.status(400).json({
        error: 'No session',
        message: 'No user session found'
      });
    }

    if (ticketType && TICKET_TYPES[ticketType]) {
      where.ticketType = ticketType;
    }

    if (isUsed !== undefined) {
      where.isUsed = isUsed === 'true';
    }

    // Get tickets with pagination
    const [tickets, total] = await Promise.all([
      prisma.generatedTicket.findMany({
        where,
        select: {
          id: true,
          ticketId: true,
          ticketType: true,
          isUsed: true,
          usedAt: true,
          includeTimestamp: true,
          metadata: true,
          createdAt: true,
          updatedAt: true
        },
        orderBy: { createdAt: 'desc' },
        skip,
        take: parseInt(limit)
      }),
      prisma.generatedTicket.count({ where })
    ]);

    // Add descriptions
    const ticketsWithDescriptions = tickets.map(ticket => ({
      ...ticket,
      description: TICKET_TYPES[ticket.ticketType]?.description || 'Unknown'
    }));

    res.json({
      success: true,
      tickets: ticketsWithDescriptions,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / parseInt(limit))
      }
    });

  } catch (error) {
    console.error('Get tickets error:', error);
    res.status(500).json({
      error: 'Failed to fetch tickets',
      message: 'An error occurred while fetching your tickets'
    });
  }
});

// Get available ticket types
router.get('/types/list', (req, res) => {
  const types = Object.entries(TICKET_TYPES).map(([key, config]) => ({
    type: key,
    prefix: config.prefix,
    description: config.description,
    exampleId: generateTicketId(key, true)
  }));

  res.json({
    success: true,
    ticketTypes: types
  });
});

// Get ticket statistics
router.get('/stats', async (req, res) => {
  try {
    const where = {};
    
    if (req.user?.id) {
      where.OR = [
        { userId: req.user.id },
        { sessionId: req.sessionId }
      ];
    } else if (req.sessionId) {
      where.sessionId = req.sessionId;
    } else {
      return res.status(400).json({
        error: 'No session',
        message: 'No user session found'
      });
    }

    // Get overall stats
    const [total, used, unused] = await Promise.all([
      prisma.generatedTicket.count({ where }),
      prisma.generatedTicket.count({ where: { ...where, isUsed: true } }),
      prisma.generatedTicket.count({ where: { ...where, isUsed: false } })
    ]);

    // Get stats by type
    const typeStats = {};
    for (const ticketType of Object.keys(TICKET_TYPES)) {
      const typeWhere = { ...where, ticketType };
      const [typeTotal, typeUsed] = await Promise.all([
        prisma.generatedTicket.count({ where: typeWhere }),
        prisma.generatedTicket.count({ where: { ...typeWhere, isUsed: true } })
      ]);
      
      typeStats[ticketType] = {
        total: typeTotal,
        used: typeUsed,
        unused: typeTotal - typeUsed
      };
    }

    res.json({
      success: true,
      stats: {
        total,
        used,
        unused,
        byType: typeStats
      }
    });

  } catch (error) {
    console.error('Get stats error:', error);
    res.status(500).json({
      error: 'Failed to fetch statistics',
      message: 'An error occurred while fetching ticket statistics'
    });
  }
});

// Validate a ticket ID
router.get('/:ticketId/validate', async (req, res) => {
  try {
    const { ticketId } = req.params;

    const ticket = await prisma.generatedTicket.findUnique({
      where: { ticketId },
      select: {
        id: true,
        ticketId: true,
        ticketType: true,
        isUsed: true,
        usedAt: true,
        createdAt: true,
        metadata: true
      }
    });

    if (!ticket) {
      return res.json({
        success: true,
        valid: false,
        message: 'Ticket not found'
      });
    }

    res.json({
      success: true,
      valid: true,
      ticket: {
        ...ticket,
        description: TICKET_TYPES[ticket.ticketType]?.description || 'Unknown'
      }
    });

  } catch (error) {
    console.error('Validate ticket error:', error);
    res.status(500).json({
      error: 'Failed to validate ticket',
      message: 'An error occurred while validating the ticket'
    });
  }
});

// Mark ticket as used
router.put('/:ticketId/use', async (req, res) => {
  try {
    const { ticketId } = req.params;

    // Find the ticket first
    const existingTicket = await prisma.generatedTicket.findUnique({
      where: { ticketId }
    });

    if (!existingTicket) {
      return res.status(404).json({
        error: 'Ticket not found',
        message: 'The specified ticket could not be found'
      });
    }

    if (existingTicket.isUsed) {
      return res.status(400).json({
        error: 'Ticket already used',
        message: 'This ticket has already been marked as used'
      });
    }

    // Mark as used
    const updatedTicket = await prisma.generatedTicket.update({
      where: { ticketId },
      data: {
        isUsed: true,
        usedAt: new Date()
      },
      select: {
        id: true,
        ticketId: true,
        ticketType: true,
        isUsed: true,
        usedAt: true,
        createdAt: true,
        metadata: true
      }
    });

    res.json({
      success: true,
      message: 'Ticket marked as used successfully',
      ticket: {
        ...updatedTicket,
        description: TICKET_TYPES[updatedTicket.ticketType]?.description || 'Unknown'
      }
    });

  } catch (error) {
    console.error('Mark ticket as used error:', error);
    res.status(500).json({
      error: 'Failed to mark ticket as used',
      message: 'An error occurred while updating the ticket'
    });
  }
});

// Enhanced search for tickets with AI recommendation tracking
router.post('/search', [
  body('ticketId')
    .optional()
    .isString()
    .withMessage('Ticket ID must be a string'),
  body('email')
    .optional()
    .isEmail()
    .withMessage('Email must be valid'),
  body('query')
    .optional()
    .isString()
    .withMessage('Search query must be a string'),
  body('recommendationData')
    .optional()
    .isObject()
    .withMessage('Recommendation data must be an object')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        message: 'Please check your input',
        details: errors.array()
      });
    }

    const { ticketId, email, query, recommendationData } = req.body;

    if (!ticketId && !email) {
      return res.status(400).json({
        error: 'Missing parameters',
        message: 'Either ticketId or email must be provided'
      });
    }

    // Track AI recommendation usage if provided
    if (recommendationData && (req.user?.id || req.sessionId)) {
      try {
        await prisma.generatedTicket.create({
          data: {
            ticketId: `AI_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`,
            ticketType: 'BOOKING_REF',
            userId: req.user?.id || null,
            sessionId: req.sessionId || null,
            metadata: {
              type: 'ai_recommendation_search',
              query: query || '',
              recommendationData: recommendationData,
              searchTimestamp: new Date().toISOString()
            }
          }
        });
      } catch (trackingError) {
        console.warn('Failed to track AI recommendation usage:', trackingError);
      }
    }

    // If searching by ticket ID
    if (ticketId) {
      const ticket = await prisma.generatedTicket.findUnique({
        where: { ticketId },
        select: {
          id: true,
          ticketId: true,
          ticketType: true,
          isUsed: true,
          usedAt: true,
          createdAt: true,
          metadata: true,
          user: {
            select: {
              email: true,
              firstName: true,
              lastName: true
            }
          }
        }
      });

      if (!ticket) {
        // Also check trip trackers
        const tracker = await prisma.tripTracker.findUnique({
          where: { trackerId: ticketId },
          include: {
            trip: {
              include: {
                destinations: true,
                routes: true
              }
            }
          }
        });

        if (tracker) {
          return res.json({
            success: true,
            type: 'trip',
            trip: tracker.trip,
            tracker: {
              trackerId: tracker.trackerId,
              email: tracker.email,
              travelerName: tracker.travelerName,
              phone: tracker.phone,
              accessCount: tracker.accessCount,
              createdAt: tracker.createdAt
            }
          });
        }

        return res.status(404).json({
          error: 'Not found',
          message: 'No ticket or trip tracker found with this ID'
        });
      }

      return res.json({
        success: true,
        type: 'ticket',
        ticket: {
          ...ticket,
          description: TICKET_TYPES[ticket.ticketType]?.description || 'Unknown'
        }
      });
    }

    // If searching by email
    if (email) {
      const [tickets, tripTrackers] = await Promise.all([
        prisma.generatedTicket.findMany({
          where: {
            user: {
              email: email
            }
          },
          select: {
            id: true,
            ticketId: true,
            ticketType: true,
            isUsed: true,
            usedAt: true,
            createdAt: true,
            metadata: true
          },
          orderBy: { createdAt: 'desc' }
        }),
        prisma.tripTracker.findMany({
          where: { email },
          include: {
            trip: {
              include: {
                destinations: true
              }
            }
          },
          orderBy: { createdAt: 'desc' }
        })
      ]);

      const ticketsWithDescriptions = tickets.map(ticket => ({
        ...ticket,
        description: TICKET_TYPES[ticket.ticketType]?.description || 'Unknown'
      }));

      return res.json({
        success: true,
        type: 'email_search',
        tickets: ticketsWithDescriptions,
        trip_trackers: tripTrackers.map(tracker => ({
          trackerId: tracker.trackerId,
          email: tracker.email,
          travelerName: tracker.travelerName,
          phone: tracker.phone,
          accessCount: tracker.accessCount,
          createdAt: tracker.createdAt,
          trip: tracker.trip
        }))
      });
    }

  } catch (error) {
    console.error('Search tickets error:', error);
    res.status(500).json({
      error: 'Search failed',
      message: 'An error occurred while searching for tickets'
    });
  }
});

// New endpoint to track AI recommendation interactions
router.post('/track-ai-interaction', [
  body('interactionType')
    .isIn(['recommendation_request', 'destination_selected', 'route_calculated', 'geocoding_used'])
    .withMessage('Invalid interaction type'),
  body('data')
    .isObject()
    .withMessage('Interaction data must be an object'),
  body('query')
    .optional()
    .isString()
    .withMessage('Query must be a string')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        message: 'Please check your input',
        details: errors.array()
      });
    }

    const { interactionType, data, query } = req.body;

    // Generate tracking ticket
    const trackingId = `TRK_${interactionType.toUpperCase()}_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;

    const trackingTicket = await prisma.generatedTicket.create({
      data: {
        ticketId: trackingId,
        ticketType: 'BOOKING_REF',
        userId: req.user?.id || null,
        sessionId: req.sessionId || null,
        metadata: {
          type: 'ai_interaction_tracking',
          interactionType,
          query: query || '',
          data,
          timestamp: new Date().toISOString(),
          userAgent: req.get('User-Agent'),
          ip: req.ip
        }
      }
    });

    res.json({
      success: true,
      message: 'AI interaction tracked successfully',
      trackingId: trackingTicket.ticketId
    });

  } catch (error) {
    console.error('Track AI interaction error:', error);
    res.status(500).json({
      error: 'Failed to track interaction',
      message: 'An error occurred while tracking the AI interaction'
    });
  }
});

// Get AI analytics
router.get('/ai-analytics', authenticateToken, requireAdmin, async (req, res) => {
  try {
    const { startDate, endDate, interactionType } = req.query;
    
    // Parse dates or use defaults (last 30 days)
    const end = endDate ? new Date(endDate) : new Date();
    const start = startDate ? new Date(startDate) : new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    
    // For now, return mock AI analytics data
    // In a real app, you would query your database for this information
    const aiAnalytics = {
      totalInteractions: 875,
      uniqueUsers: 342,
      averageInteractionsPerUser: 2.56,
      interactionTypes: {
        recommendation_request: 623,
        destination_selected: 187,
        route_calculation: 65
      },
      popularQueries: [
        { query: "beaches in the philippines", count: 87 },
        { query: "mountain hiking", count: 62 },
        { query: "best restaurants in manila", count: 55 },
        { query: "tourist spots in cebu", count: 48 },
        { query: "boracay activities", count: 43 }
      ],
      responseMetrics: {
        averageResponseTime: 1.2, // seconds
        successRate: 98.5 // percentage
      },
      interactionsByDay: {
        // Mock data for daily interactions over the past week
        "2023-05-26": 32,
        "2023-05-27": 45,
        "2023-05-28": 56,
        "2023-05-29": 41,
        "2023-05-30": 38,
        "2023-05-31": 29,
        "2023-06-01": 35,
        "2023-06-02": 42
      },
      recentInteractions: [
        {
          id: "ai-int-1001",
          type: "recommendation_request",
          query: "hiking spots near baguio",
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          responseCount: 5,
          userId: 42
        },
        {
          id: "ai-int-1002",
          type: "destination_selected",
          query: "beaches in palawan",
          timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
          selectedDestination: "El Nido",
          userId: 28
        },
        {
          id: "ai-int-1003",
          type: "route_calculation",
          timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
          points: 4,
          distance: "12.5 km",
          userId: 75
        }
      ]
    };
    
    res.json({
      success: true,
      analytics: aiAnalytics
    });
  } catch (error) {
    console.error('AI analytics error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get analytics',
      message: 'An error occurred while fetching AI analytics'
    });
  }
});

module.exports = router; 