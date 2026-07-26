-- ============================================
-- Royal Brothers Fitness Gym - Full Database Schema
-- Use this to set up a BRAND NEW database from scratch
-- (fresh installs, new deployments, CI/test databases).
--
-- If you already have an existing royal_brothers_gym database with
-- data in it, do NOT run this file -- use schema_updates.sql instead,
-- which only adds the new columns/table without touching your data.
-- ============================================

CREATE DATABASE IF NOT EXISTS royal_brothers_gym
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

USE royal_brothers_gym;

-- ---------- ADMINS ----------
CREATE TABLE IF NOT EXISTS admins (
  id INT NOT NULL AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------- USERS ----------
CREATE TABLE IF NOT EXISTS users (
  id INT NOT NULL AUTO_INCREMENT,
  full_name VARCHAR(100) NOT NULL,
  email VARCHAR(150) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  gender ENUM('male', 'female', 'other') NOT NULL,
  google_id VARCHAR(255) DEFAULT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  profile_photo VARCHAR(255) DEFAULT NULL,
  is_verified TINYINT(1) NOT NULL DEFAULT 0
    COMMENT 'Set to 1 only after the user clicks their email verification link',
  failed_login_attempts INT NOT NULL DEFAULT 0
    COMMENT 'Consecutive wrong-password count, reset to 0 on successful login',
  lockout_until DATETIME NULL
    COMMENT 'If set and in the future, login is blocked until this time',
  PRIMARY KEY (id),
  UNIQUE KEY email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------- MEMBERSHIP PLANS ----------
CREATE TABLE IF NOT EXISTS membership_plans (
  id INT NOT NULL AUTO_INCREMENT,
  plan_name VARCHAR(50) NOT NULL,
  duration_months INT NOT NULL,
  price DECIMAL(10, 2) NOT NULL,
  features TEXT,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------- MEMBERSHIP REQUESTS ----------
CREATE TABLE IF NOT EXISTS membership_requests (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  plan_id INT NOT NULL,
  status ENUM('pending', 'active', 'rejected') DEFAULT 'pending',
  request_date TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  start_date DATE DEFAULT NULL,
  end_date DATE DEFAULT NULL,
  PRIMARY KEY (id),
  KEY user_id (user_id),
  KEY plan_id (plan_id),
  CONSTRAINT membership_requests_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT membership_requests_ibfk_2 FOREIGN KEY (plan_id) REFERENCES membership_plans (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------- CONTACT MESSAGES ----------
CREATE TABLE IF NOT EXISTS contact_messages (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  email VARCHAR(150) NOT NULL,
  subject VARCHAR(50) NOT NULL,
  message TEXT NOT NULL,
  is_read TINYINT(1) DEFAULT '0',
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------- PASSWORD RESET TOKENS ----------
CREATE TABLE IF NOT EXISTS password_reset_tokens (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  token_hash VARCHAR(64) NOT NULL,
  expires_at DATETIME NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY token_hash (token_hash),
  KEY fk_password_reset_user (user_id),
  KEY idx_password_reset_token_hash (token_hash),
  CONSTRAINT fk_password_reset_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------- EMAIL VERIFICATION TOKENS ----------
CREATE TABLE IF NOT EXISTS email_verification_tokens (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  token_hash VARCHAR(64) NOT NULL,
  expires_at DATETIME NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY token_hash (token_hash),
  KEY fk_email_verification_user (user_id),
  KEY idx_email_verification_token_hash (token_hash),
  CONSTRAINT fk_email_verification_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
