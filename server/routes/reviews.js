const express = require('express');
const { body, validationResult } = require('express-validator');
const { PrismaClient } = require('@prisma/client');
const { optionalAuth } = require('../middleware/auth');

const router = express.Router();
const prisma = new PrismaClient();

// Apply optional auth to all routes
router.use(optionalAuth);

// Validation rules
const reviewValidation = [
  body('tripId')
    .notEmpty()
    .withMessage('Trip ID is required')
    .isLength({ max: 36 })
    .withMessage('Invalid trip ID'),
  body('reviewerName')
    .notEmpty()
    .withMessage('Reviewer name is required')
    .isLength({ min: 2, max: 255 })
    .withMessage('Reviewer name must be between 2 and 255 characters'),
  body('rating')
    .isInt({ min: 1, max: 5 })
    .withMessage('Rating must be between 1 and 5'),
  body('reviewText')
    .notEmpty()
    .withMessage('Review text is required')
    .isLength({ min: 10, max: 2000 })
    .withMessage('Review text must be between 10 and 2000 characters'),
  body('email')
    .optional()
    .isEmail()
    .normalizeEmail()
    .withMessage('Please provide a valid email')
];

// Create a new review
router.post('/', reviewValidation, async (req, res) => {
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

    const { tripId, reviewerName, rating, reviewText, email } = req.body;

    // Check if trip exists (optional - you might want to verify this against your trips table)
    // For now, we'll just create the review

    // Create review
    const review = await prisma.tripReview.create({
      data: {
        tripId,
        reviewerName,
        rating,
        reviewText,
        email: email || null
      },
      select: {
        id: true,
        tripId: true,
        reviewerName: true,
        rating: true,
        reviewText: true,
        isApproved: true,
        createdAt: true,
        updatedAt: true
      }
    });

    res.status(201).json({
      success: true,
      message: 'Review created successfully',
      review
    });

  } catch (error) {
    console.error('Create review error:', error);
    res.status(500).json({
      error: 'Failed to create review',
      message: 'An error occurred while creating the review'
    });
  }
});

// Get reviews for a trip
router.get('/trip/:tripId', async (req, res) => {
  try {
    const { tripId } = req.params;
    const { page = 1, limit = 20, approved = 'true' } = req.query;
    const skip = (parseInt(page) - 1) * parseInt(limit);

    // Build where clause
    const where = { tripId };
    
    // Only show approved reviews by default
    if (approved === 'true') {
      where.isApproved = true;
    }

    // Get reviews with pagination
    const [reviews, total] = await Promise.all([
      prisma.tripReview.findMany({
        where,
        select: {
          id: true,
          reviewerName: true,
          rating: true,
          reviewText: true,
          isApproved: true,
          createdAt: true,
          updatedAt: true
        },
        orderBy: { createdAt: 'desc' },
        skip,
        take: parseInt(limit)
      }),
      prisma.tripReview.count({ where })
    ]);

    // Calculate average rating
    const avgRating = await prisma.tripReview.aggregate({
      where: { tripId, isApproved: true },
      _avg: {
        rating: true
      }
    });

    res.json({
      success: true,
      reviews,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / parseInt(limit))
      },
      stats: {
        totalReviews: total,
        averageRating: avgRating._avg.rating ? parseFloat(avgRating._avg.rating.toFixed(1)) : 0
      }
    });

  } catch (error) {
    console.error('Get reviews error:', error);
    res.status(500).json({
      error: 'Failed to fetch reviews',
      message: 'An error occurred while fetching reviews'
    });
  }
});

// Get review statistics for a trip
router.get('/trip/:tripId/stats', async (req, res) => {
  try {
    const { tripId } = req.params;

    // Get review statistics
    const [totalReviews, avgRating, ratingDistribution] = await Promise.all([
      prisma.tripReview.count({
        where: { tripId, isApproved: true }
      }),
      prisma.tripReview.aggregate({
        where: { tripId, isApproved: true },
        _avg: { rating: true }
      }),
      prisma.tripReview.groupBy({
        by: ['rating'],
        where: { tripId, isApproved: true },
        _count: { rating: true },
        orderBy: { rating: 'desc' }
      })
    ]);

    // Format rating distribution
    const distribution = {};
    for (let i = 1; i <= 5; i++) {
      distribution[i] = 0;
    }
    ratingDistribution.forEach(item => {
      distribution[item.rating] = item._count.rating;
    });

    res.json({
      success: true,
      stats: {
        totalReviews,
        averageRating: avgRating._avg.rating ? parseFloat(avgRating._avg.rating.toFixed(1)) : 0,
        ratingDistribution: distribution
      }
    });

  } catch (error) {
    console.error('Get review stats error:', error);
    res.status(500).json({
      error: 'Failed to fetch review statistics',
      message: 'An error occurred while fetching review statistics'
    });
  }
});

// Get a specific review
router.get('/:reviewId', async (req, res) => {
  try {
    const { reviewId } = req.params;

    const review = await prisma.tripReview.findUnique({
      where: { id: parseInt(reviewId) },
      select: {
        id: true,
        tripId: true,
        reviewerName: true,
        rating: true,
        reviewText: true,
        isApproved: true,
        createdAt: true,
        updatedAt: true
      }
    });

    if (!review) {
      return res.status(404).json({
        error: 'Review not found',
        message: 'The specified review could not be found'
      });
    }

    // Only show approved reviews to public
    if (!review.isApproved) {
      return res.status(404).json({
        error: 'Review not found',
        message: 'The specified review could not be found'
      });
    }

    res.json({
      success: true,
      review
    });

  } catch (error) {
    console.error('Get review error:', error);
    res.status(500).json({
      error: 'Failed to fetch review',
      message: 'An error occurred while fetching the review'
    });
  }
});

// Update review approval status (admin function)
router.put('/:reviewId/approve', async (req, res) => {
  try {
    const { reviewId } = req.params;
    const { isApproved } = req.body;

    // Note: In a real application, you'd want to add admin authentication here
    // For now, this is a simple approval toggle

    const review = await prisma.tripReview.findUnique({
      where: { id: parseInt(reviewId) }
    });

    if (!review) {
      return res.status(404).json({
        error: 'Review not found',
        message: 'The specified review could not be found'
      });
    }

    const updatedReview = await prisma.tripReview.update({
      where: { id: parseInt(reviewId) },
      data: { isApproved: Boolean(isApproved) },
      select: {
        id: true,
        tripId: true,
        reviewerName: true,
        rating: true,
        reviewText: true,
        isApproved: true,
        createdAt: true,
        updatedAt: true
      }
    });

    res.json({
      success: true,
      message: `Review ${isApproved ? 'approved' : 'unapproved'} successfully`,
      review: updatedReview
    });

  } catch (error) {
    console.error('Update review approval error:', error);
    res.status(500).json({
      error: 'Failed to update review approval',
      message: 'An error occurred while updating the review'
    });
  }
});

// Delete a review
router.delete('/:reviewId', async (req, res) => {
  try {
    const { reviewId } = req.params;

    // Note: In a real application, you'd want to add proper authorization here
    // to ensure only the review author or admin can delete

    const review = await prisma.tripReview.findUnique({
      where: { id: parseInt(reviewId) }
    });

    if (!review) {
      return res.status(404).json({
        error: 'Review not found',
        message: 'The specified review could not be found'
      });
    }

    await prisma.tripReview.delete({
      where: { id: parseInt(reviewId) }
    });

    res.json({
      success: true,
      message: 'Review deleted successfully'
    });

  } catch (error) {
    console.error('Delete review error:', error);
    res.status(500).json({
      error: 'Failed to delete review',
      message: 'An error occurred while deleting the review'
    });
  }
});

// Get recent reviews (across all trips)
router.get('/recent/all', async (req, res) => {
  try {
    const { limit = 10 } = req.query;

    const reviews = await prisma.tripReview.findMany({
      where: { isApproved: true },
      select: {
        id: true,
        tripId: true,
        reviewerName: true,
        rating: true,
        reviewText: true,
        createdAt: true
      },
      orderBy: { createdAt: 'desc' },
      take: parseInt(limit)
    });

    res.json({
      success: true,
      reviews
    });

  } catch (error) {
    console.error('Get recent reviews error:', error);
    res.status(500).json({
      error: 'Failed to fetch recent reviews',
      message: 'An error occurred while fetching recent reviews'
    });
  }
});

// Search reviews
router.get('/search/query', async (req, res) => {
  try {
    const { q, tripId, rating, page = 1, limit = 20 } = req.query;
    const skip = (parseInt(page) - 1) * parseInt(limit);

    // Build where clause
    const where = { isApproved: true };

    if (tripId) {
      where.tripId = tripId;
    }

    if (rating) {
      where.rating = parseInt(rating);
    }

    if (q) {
      where.OR = [
        { reviewText: { contains: q } },
        { reviewerName: { contains: q } }
      ];
    }

    // Get reviews with pagination
    const [reviews, total] = await Promise.all([
      prisma.tripReview.findMany({
        where,
        select: {
          id: true,
          tripId: true,
          reviewerName: true,
          rating: true,
          reviewText: true,
          createdAt: true
        },
        orderBy: { createdAt: 'desc' },
        skip,
        take: parseInt(limit)
      }),
      prisma.tripReview.count({ where })
    ]);

    res.json({
      success: true,
      reviews,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / parseInt(limit))
      },
      query: { q, tripId, rating }
    });

  } catch (error) {
    console.error('Search reviews error:', error);
    res.status(500).json({
      error: 'Failed to search reviews',
      message: 'An error occurred while searching reviews'
    });
  }
});

module.exports = router; 