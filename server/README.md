# WerTigo Express Backend

Express.js backend for WerTigo travel planner with Prisma ORM, handling authentication, ticket tracking, reviews, and trip sharing functionality.

## Features

- 🔐 **Authentication**: User registration, login, JWT-based authentication
- 🎫 **Ticket Management**: Generate and track travel tickets (flights, buses, hotels, etc.)
- ⭐ **Reviews System**: Trip reviews and ratings with approval workflow
- 📍 **Trip Tracking**: Shareable trip trackers with access control
- 🛡️ **Security**: Rate limiting, input validation, CORS protection
- 📊 **Database**: MySQL with Prisma ORM for type-safe database operations

## Tech Stack

- **Framework**: Express.js
- **Database**: MySQL with Prisma ORM
- **Authentication**: JWT (JSON Web Tokens)
- **Validation**: express-validator
- **Security**: Helmet, CORS, Rate limiting
- **Password Hashing**: bcryptjs

## Prerequisites

- Node.js 16+ 
- MySQL 8.0+
- npm or yarn

## Installation

1. **Clone and navigate to the Express backend directory:**
   ```bash
   cd server-express
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   DATABASE_URL="mysql://username:password@localhost:3306/wertigo_db"
   JWT_SECRET="your-super-secret-jwt-key"
   PORT=3001
   ```

4. **Set up the database:**
   ```bash
   # Generate Prisma client
   npm run db:generate
   
   # Push schema to database (creates tables)
   npm run db:push
   
   # Or run migrations (recommended for production)
   npm run db:migrate
   ```

5. **Start the server:**
   ```bash
   # Development mode with auto-reload
   npm run dev
   
   # Production mode
   npm start
   ```

## API Endpoints

### Authentication (`/api/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/register` | Register new user | No |
| POST | `/login` | User login | No |
| GET | `/profile` | Get user profile | Yes |
| PUT | `/profile` | Update user profile | Yes |
| PUT | `/change-password` | Change password | Yes |
| GET | `/verify` | Verify JWT token | Yes |
| POST | `/logout` | Logout user | Yes |

### Tickets (`/api/tickets`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/generate` | Generate new ticket | Optional |
| GET | `/my-tickets` | Get user's tickets | Optional |
| GET | `/types/list` | Get available ticket types | No |
| GET | `/:ticketId` | Get specific ticket | Optional |
| PUT | `/:ticketId/use` | Mark ticket as used | Optional |
| GET | `/stats/summary` | Get ticket statistics | Optional |
| DELETE | `/clear-all` | Clear all user tickets | Optional |

### Reviews (`/api/reviews`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/` | Create new review | No |
| GET | `/trip/:tripId` | Get reviews for trip | No |
| GET | `/trip/:tripId/stats` | Get review statistics | No |
| GET | `/:reviewId` | Get specific review | No |
| PUT | `/:reviewId/approve` | Approve/unapprove review | No* |
| DELETE | `/:reviewId` | Delete review | No* |
| GET | `/recent/all` | Get recent reviews | No |
| GET | `/search/query` | Search reviews | No |

*Note: In production, these should require admin authentication

### Trip Trackers (`/api/trackers`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/` | Create trip tracker | Optional |
| GET | `/:trackerId` | Get trip by tracker ID | No |
| GET | `/email/:email` | Get trackers by email | No |
| PUT | `/:trackerId` | Update tracker | No |
| DELETE | `/:trackerId` | Deactivate tracker | No |
| GET | `/:trackerId/stats` | Get tracker statistics | No |
| GET | `/:trackerId/validate` | Validate tracker | No |

## Database Schema

The application uses the following main models:

- **User**: User accounts with authentication
- **Trip**: Trip information with destinations and routes
- **TripDestination**: Individual destinations within trips
- **TripRoute**: Route data between destinations
- **GeneratedTicket**: Generated travel tickets
- **TripTracker**: Shareable trip tracking links
- **TripReview**: User reviews and ratings for trips

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | MySQL connection string | Required |
| `JWT_SECRET` | Secret key for JWT tokens | Required |
| `JWT_EXPIRES_IN` | JWT token expiration | `7d` |
| `PORT` | Server port | `3001` |
| `NODE_ENV` | Environment mode | `development` |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:3000` |
| `PYTHON_BACKEND_URL` | Python backend URL | `http://localhost:5000` |

## Development

### Database Operations

```bash
# Generate Prisma client after schema changes
npm run db:generate

# Push schema changes to database (development)
npm run db:push

# Create and run migrations (production)
npm run db:migrate

# Open Prisma Studio (database GUI)
npm run db:studio

# Seed database with sample data
npm run db:seed
```

### Code Structure

```
server-express/
├── prisma/
│   ├── schema.prisma      # Database schema
│   └── seed.js           # Database seeding
├── routes/
│   ├── auth.js           # Authentication routes
│   ├── tickets.js        # Ticket management
│   ├── reviews.js        # Review system
│   └── trackers.js       # Trip tracking
├── middleware/
│   └── auth.js           # Authentication middleware
├── server.js             # Main server file
└── package.json          # Dependencies and scripts
```

## Security Features

- **Rate Limiting**: Prevents API abuse
- **Input Validation**: Validates all user inputs
- **Password Hashing**: Uses bcrypt with salt rounds
- **JWT Authentication**: Secure token-based auth
- **CORS Protection**: Configurable cross-origin requests
- **Helmet**: Security headers middleware

## Integration with Python Backend

This Express backend works alongside the Python Flask backend:

- **Python Backend** (Port 5000): Handles AI recommendations, trip planning, route calculation
- **Express Backend** (Port 3001): Handles authentication, tickets, reviews, trip sharing

The frontends can communicate with both backends as needed.

## Error Handling

The API returns consistent error responses:

```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "details": [] // Optional validation details
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details 