-- --------------------------------------------------------
-- Хост:                         172.18.11.104
-- Версия сервера:               8.0.37 - MySQL Community Server - GPL
-- Операционная система:         Linux
-- HeidiSQL Версия:              12.14.0.7165
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Дамп структуры базы данных mdtomskbot
CREATE DATABASE IF NOT EXISTS `mdtomskbot` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `mdtomskbot`;

-- Дамп структуры для таблица mdtomskbot.agreement
CREATE TABLE IF NOT EXISTS `agreement` (
  `id_vk` bigint DEFAULT NULL,
  `id_tb` bigint DEFAULT NULL,
  `vk` tinyint DEFAULT NULL,
  `tb` tinyint DEFAULT NULL,
  `tel` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.anniversary
CREATE TABLE IF NOT EXISTS `anniversary` (
  `id` int NOT NULL AUTO_INCREMENT,
  `text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `date` text,
  `sender` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  UNIQUE KEY `Столбец 1` (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=270 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.application
CREATE TABLE IF NOT EXISTS `application` (
  `id` int NOT NULL AUTO_INCREMENT,
  `fio` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `contacts` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `type_service` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `service` text,
  `date` text,
  `category` text,
  UNIQUE KEY `Столбец 1` (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=134 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.base_1C
CREATE TABLE IF NOT EXISTS `base_1C` (
  `date` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `sum` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `agreement` text,
  `counterparty` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.calendar
CREATE TABLE IF NOT EXISTS `calendar` (
  `location` text,
  `date` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.count_tb
CREATE TABLE IF NOT EXISTS `count_tb` (
  `id` text,
  `date` text,
  `time` text,
  `button` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.count_vk
CREATE TABLE IF NOT EXISTS `count_vk` (
  `id` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `date` text,
  `time` text,
  `button` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.cpgu_order_statuses
CREATE TABLE IF NOT EXISTS `cpgu_order_statuses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` text,
  `code` text,
  `status` text,
  `district` text,
  `address` text,
  `execution` text,
  `date` datetime DEFAULT NULL,
  `phone` text,
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1189 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.events
CREATE TABLE IF NOT EXISTS `events` (
  `id_vk` bigint DEFAULT NULL,
  `id_tb` bigint DEFAULT NULL,
  `event` text,
  `date` text,
  `platform` text,
  `now` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.feedback
CREATE TABLE IF NOT EXISTS `feedback` (
  `tel` text,
  `date` text,
  `time` text,
  `utterance` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.file_id_tb
CREATE TABLE IF NOT EXISTS `file_id_tb` (
  `id_tb` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `file` text,
  `file_format` text,
  `marker` text,
  `message` text,
  `phone` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.file_tb
CREATE TABLE IF NOT EXISTS `file_tb` (
  `ani` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `datetime` datetime DEFAULT NULL,
  `processed` tinyint(1) DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.notification
CREATE TABLE IF NOT EXISTS `notification` (
  `ani` varchar(50) DEFAULT NULL,
  `id_vk` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `id_tb` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `date` text,
  `new_ani` text,
  `restrictions` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  UNIQUE KEY `ani` (`ani`),
  UNIQUE KEY `id_vk` (`id_vk`),
  UNIQUE KEY `id_tb` (`id_tb`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.person_data
CREATE TABLE IF NOT EXISTS `person_data` (
  `ani` bigint NOT NULL DEFAULT '0',
  UNIQUE KEY `id` (`ani`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.ratings_reviews
CREATE TABLE IF NOT EXISTS `ratings_reviews` (
  `number_statement` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `number_date` text,
  `number_department` text,
  `number_grade` text,
  `number_waiting_time` text,
  `number_time` text,
  `number_employee` text,
  `number_review` text,
  `date_now` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.send_vk
CREATE TABLE IF NOT EXISTS `send_vk` (
  `ani` text,
  `message` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.staffing_analysis
CREATE TABLE IF NOT EXISTS `staffing_analysis` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_one_c` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `department` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  `planned` decimal(10,2) NOT NULL DEFAULT '0.00',
  `free` decimal(10,2) NOT NULL DEFAULT '0.00',
  `accepted` decimal(10,2) NOT NULL DEFAULT '0.00',
  `fired` decimal(10,2) NOT NULL DEFAULT '0.00',
  `vacations` decimal(10,2) NOT NULL DEFAULT '0.00',
  `hospital` decimal(10,2) NOT NULL DEFAULT '0.00',
  `date` date NOT NULL,
  `dep_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_idone_c_date` (`id_one_c`,`date`)
) ENGINE=InnoDB AUTO_INCREMENT=5531 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.telegram_reg
CREATE TABLE IF NOT EXISTS `telegram_reg` (
  `ani` text,
  `talon` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `time` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `date` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `department` text,
  `service` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `uuid` text,
  `tel` text,
  `fio` text,
  `now` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.treatment
CREATE TABLE IF NOT EXISTS `treatment` (
  `id` smallint NOT NULL AUTO_INCREMENT,
  `text` text,
  `date` text,
  `time` text,
  `platform` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.treatment_reg
CREATE TABLE IF NOT EXISTS `treatment_reg` (
  `id` smallint NOT NULL AUTO_INCREMENT,
  `url` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `date` text,
  `time` text,
  `platform` text,
  `talon` text,
  `date_talon` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `time_talon` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `service` text,
  `department` text,
  `fio` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица mdtomskbot.vkontakte_reg
CREATE TABLE IF NOT EXISTS `vkontakte_reg` (
  `sender` text,
  `talon` text,
  `time` text,
  `date` text,
  `department` text,
  `service` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `uuid` text,
  `tel` text,
  `fio` text,
  `now` text,
  `service_id` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Экспортируемые данные не выделены.

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
