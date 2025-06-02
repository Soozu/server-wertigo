-- CreateTable
CREATE TABLE `users` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `username` VARCHAR(50) NOT NULL,
    `email` VARCHAR(100) NOT NULL,
    `password` VARCHAR(255) NOT NULL,
    `first_name` VARCHAR(50) NULL,
    `last_name` VARCHAR(50) NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updated_at` DATETIME(3) NOT NULL,

    UNIQUE INDEX `users_username_key`(`username`),
    UNIQUE INDEX `users_email_key`(`email`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `user_sessions` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `user_id` INTEGER NOT NULL,
    `session_id` VARCHAR(255) NOT NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `expires_at` DATETIME(3) NOT NULL,

    UNIQUE INDEX `user_sessions_session_id_key`(`session_id`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `trips` (
    `id` VARCHAR(36) NOT NULL,
    `user_id` INTEGER NULL,
    `session_id` VARCHAR(255) NULL,
    `trip_name` VARCHAR(100) NULL,
    `destination` VARCHAR(100) NULL,
    `start_date` DATE NULL,
    `end_date` DATE NULL,
    `budget` DECIMAL(10, 2) NULL,
    `travelers` INTEGER NOT NULL DEFAULT 1,
    `status` ENUM('active', 'completed', 'cancelled') NOT NULL DEFAULT 'active',
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updated_at` DATETIME(3) NOT NULL,

    INDEX `idx_session_id`(`session_id`),
    INDEX `idx_user_id`(`user_id`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `trip_destinations` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `trip_id` VARCHAR(36) NOT NULL,
    `destination_id` INTEGER NULL,
    `name` VARCHAR(255) NOT NULL,
    `city` VARCHAR(100) NULL,
    `province` VARCHAR(100) NULL,
    `description` TEXT NULL,
    `category` VARCHAR(50) NULL,
    `rating` DECIMAL(3, 2) NULL,
    `budget` DECIMAL(10, 2) NULL,
    `latitude` DECIMAL(10, 8) NULL,
    `longitude` DECIMAL(11, 8) NULL,
    `operating_hours` VARCHAR(255) NULL,
    `contact_information` VARCHAR(255) NULL,
    `order_index` INTEGER NOT NULL DEFAULT 0,
    `added_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

    INDEX `idx_trip_id`(`trip_id`),
    INDEX `idx_order`(`trip_id`, `order_index`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `trip_routes` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `trip_id` VARCHAR(36) NOT NULL,
    `route_data` JSON NULL,
    `distance_km` DECIMAL(8, 2) NULL,
    `time_minutes` INTEGER NULL,
    `route_source` VARCHAR(50) NULL,
    `calculated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

    INDEX `idx_trip_id`(`trip_id`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `saved_trips` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `user_id` INTEGER NOT NULL,
    `trip_name` VARCHAR(100) NOT NULL,
    `destination` VARCHAR(100) NULL,
    `start_date` DATE NULL,
    `end_date` DATE NULL,
    `budget` DECIMAL(10, 2) NULL,
    `travelers` INTEGER NOT NULL DEFAULT 1,
    `trip_data` JSON NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updated_at` DATETIME(3) NOT NULL,

    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `user_preferences` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `user_id` INTEGER NOT NULL,
    `preference_key` VARCHAR(50) NOT NULL,
    `preference_value` TEXT NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updated_at` DATETIME(3) NOT NULL,

    UNIQUE INDEX `user_preference`(`user_id`, `preference_key`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `generated_tickets` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `ticket_id` VARCHAR(50) NOT NULL,
    `ticket_type` ENUM('FLIGHT', 'BUS', 'FERRY', 'TRAIN', 'HOTEL', 'TOUR', 'BOOKING_REF', 'CONFIRMATION') NOT NULL,
    `user_id` INTEGER NULL,
    `session_id` VARCHAR(255) NULL,
    `is_used` BOOLEAN NOT NULL DEFAULT false,
    `used_at` DATETIME(3) NULL,
    `include_timestamp` BOOLEAN NOT NULL DEFAULT true,
    `metadata` JSON NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updated_at` DATETIME(3) NOT NULL,

    UNIQUE INDEX `generated_tickets_ticket_id_key`(`ticket_id`),
    INDEX `idx_ticket_id`(`ticket_id`),
    INDEX `idx_user_id`(`user_id`),
    INDEX `idx_session_id`(`session_id`),
    INDEX `idx_ticket_type`(`ticket_type`),
    INDEX `idx_created_at`(`created_at`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `trip_trackers` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `tracker_id` VARCHAR(50) NOT NULL,
    `trip_id` VARCHAR(36) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `traveler_name` VARCHAR(255) NULL,
    `phone` VARCHAR(50) NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT true,
    `access_count` INTEGER NOT NULL DEFAULT 0,
    `last_accessed` DATETIME(3) NULL,
    `expires_at` DATETIME(3) NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updated_at` DATETIME(3) NOT NULL,

    UNIQUE INDEX `trip_trackers_tracker_id_key`(`tracker_id`),
    INDEX `idx_tracker_id`(`tracker_id`),
    INDEX `idx_trip_id`(`trip_id`),
    INDEX `idx_email`(`email`),
    INDEX `idx_created_at`(`created_at`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `trip_reviews` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `trip_id` VARCHAR(36) NOT NULL,
    `reviewer_name` VARCHAR(255) NOT NULL,
    `rating` TINYINT NOT NULL,
    `review_text` TEXT NOT NULL,
    `email` VARCHAR(255) NULL,
    `is_approved` BOOLEAN NOT NULL DEFAULT true,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updated_at` DATETIME(3) NOT NULL,

    INDEX `idx_trip_id`(`trip_id`),
    INDEX `idx_rating`(`rating`),
    INDEX `idx_created_at`(`created_at`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- AddForeignKey
ALTER TABLE `user_sessions` ADD CONSTRAINT `user_sessions_user_id_fkey` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `trips` ADD CONSTRAINT `trips_user_id_fkey` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `trip_destinations` ADD CONSTRAINT `trip_destinations_trip_id_fkey` FOREIGN KEY (`trip_id`) REFERENCES `trips`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `trip_routes` ADD CONSTRAINT `trip_routes_trip_id_fkey` FOREIGN KEY (`trip_id`) REFERENCES `trips`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `saved_trips` ADD CONSTRAINT `saved_trips_user_id_fkey` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `user_preferences` ADD CONSTRAINT `user_preferences_user_id_fkey` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `generated_tickets` ADD CONSTRAINT `generated_tickets_user_id_fkey` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `trip_trackers` ADD CONSTRAINT `trip_trackers_trip_id_fkey` FOREIGN KEY (`trip_id`) REFERENCES `trips`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;
