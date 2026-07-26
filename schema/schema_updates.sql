-- ============================================
-- Royal Brothers Fitness Gym - Schema Updates
-- Use this ONLY if you already have an existing royal_brothers_gym
-- database with data in it. Adds email verification + login lockout
-- support without touching existing rows.
--
-- For a brand new database, use schema.sql instead (it already
-- includes these columns/table from the start).
-- ============================================

-- ---------- USERS: email verification + lockout tracking ----------
ALTER TABLE `users`
    ADD COLUMN `is_verified` TINYINT(1) NOT NULL DEFAULT 0
        COMMENT 'Set to 1 only after the user clicks their email verification link',
    ADD COLUMN `failed_login_attempts` INT NOT NULL DEFAULT 0
        COMMENT 'Consecutive wrong-password count, reset to 0 on successful login',
    ADD COLUMN `lockout_until` DATETIME NULL
        COMMENT 'If set and in the future, login is blocked until this time';

-- ---------- EMAIL VERIFICATION TOKENS ----------
CREATE TABLE `email_verification_tokens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `token_hash` varchar(64) NOT NULL,
  `expires_at` datetime NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token_hash` (`token_hash`),
  KEY `fk_email_verification_user` (`user_id`),
  KEY `idx_email_verification_token_hash` (`token_hash`),
  CONSTRAINT `fk_email_verification_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------- Grandfather in existing real accounts ----------
-- Without this, every account that existed before this migration
-- would suddenly be unverified and locked out of login. Uncomment if
-- you have real existing members using the site:
-- UPDATE `users` SET `is_verified` = 1;
