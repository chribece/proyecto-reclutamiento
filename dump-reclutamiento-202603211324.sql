/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.7.2-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: reclutamiento
-- ------------------------------------------------------
-- Server version	12.1.2-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `candidatos`
--

DROP TABLE IF EXISTS `candidatos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `candidatos` (
  `cedula` varchar(10) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `apellido` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `resumen` text DEFAULT NULL,
  `habilidades` text DEFAULT NULL,
  `experiencia_anos` int(11) DEFAULT 0,
  `nivel_educativo` varchar(100) DEFAULT NULL,
  `ubicacion` varchar(100) DEFAULT NULL,
  `disponibilidad` varchar(50) DEFAULT NULL,
  `salario_esperado` decimal(10,2) DEFAULT NULL,
  `fecha_registro` timestamp NULL DEFAULT current_timestamp(),
  `activo` tinyint(1) DEFAULT 1,
  `curriculum_path` varchar(255) DEFAULT NULL,
  `licencia` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`cedula`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_cedula` (`cedula`),
  KEY `idx_email` (`email`),
  KEY `idx_activo` (`activo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `candidatos`
--

LOCK TABLES `candidatos` WRITE;
/*!40000 ALTER TABLE `candidatos` DISABLE KEYS */;
INSERT INTO `candidatos` VALUES
('0904258740','Darwin','Sanchez','prueba3@gmail.com',NULL,NULL,0,NULL,'Pomasqui',NULL,NULL,'2026-03-16 00:24:18',1,'uploads/curriculum/0904258740_Darwin_Sanchez.pdf',NULL),
('0912345678','Juan','Perez Garcia','juan.perez@correo.com',NULL,NULL,0,NULL,NULL,NULL,NULL,'2026-03-15 19:53:58',1,NULL,NULL),
('1114587542','Saul','Segovia','papeles@gmail.com',NULL,NULL,0,NULL,'Sur',NULL,NULL,'2026-03-16 01:03:20',1,'uploads/curriculum/1114587542_Saul_Segovia.pdf','B'),
('1234567890','María','González','maria.gonzalez@gmail.com',NULL,NULL,0,NULL,'Quito, Pichincha',NULL,NULL,'2026-03-16 00:49:07',1,NULL,'C'),
('1402548570','Juana','Valladares','Chrisp@hotmail.com',NULL,NULL,0,NULL,'Sur',NULL,NULL,'2026-03-15 23:33:44',1,NULL,NULL),
('1714341813','Vladimir','Becerra','krisvladbec@gmail.com',NULL,NULL,0,NULL,NULL,NULL,NULL,'2026-03-15 19:53:58',1,NULL,NULL),
('9999999999','Juan','Pérez','test.candidato@example.com',NULL,NULL,0,NULL,'Quito',NULL,NULL,'2026-03-16 00:47:13',1,NULL,'B');
/*!40000 ALTER TABLE `candidatos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cargos`
--

DROP TABLE IF EXISTS `cargos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `cargos` (
  `id_cargo` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `departamento` varchar(100) DEFAULT NULL,
  `salario_minimo` decimal(10,2) DEFAULT NULL,
  `salario_maximo` decimal(10,2) DEFAULT NULL,
  `tipo_contrato` varchar(50) DEFAULT NULL,
  `ubicacion` varchar(100) DEFAULT NULL,
  `id_sucursal` int(11) DEFAULT NULL,
  `estado` varchar(50) DEFAULT 'Activo',
  `fecha_creacion` timestamp NULL DEFAULT current_timestamp(),
  `fecha_cierre` date DEFAULT NULL,
  PRIMARY KEY (`id_cargo`),
  KEY `idx_estado` (`estado`),
  KEY `idx_departamento` (`departamento`),
  KEY `fk_cargos_sucursal` (`id_sucursal`),
  CONSTRAINT `fk_cargos_sucursal` FOREIGN KEY (`id_sucursal`) REFERENCES `sucursales` (`id_sucursal`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cargos`
--

LOCK TABLES `cargos` WRITE;
/*!40000 ALTER TABLE `cargos` DISABLE KEYS */;
INSERT INTO `cargos` VALUES
(2,'Especialista en Marketing Digital','Experiencia en redes sociales y campaÃ±as digitales','Marketing',1800.00,3000.00,'Tiempo completo','Quito',1,'Activo','2026-03-15 18:12:34',NULL),
(3,'Contador General','Contabilidad, impuestos y auditorÃ­a','Finanzas',1500.00,2800.00,'Tiempo completo','Quito',1,'Pausado','2026-03-15 18:12:34',NULL),
(4,'Motorizado - Repartidor','Entrega y recepción de repuestos ','Operacciones',500.00,700.00,'Tiempo completo','Calderon',1,'Activo','2026-03-15 22:35:52','2026-03-16'),
(5,'Bodeguero','Recepción, ingreso y monitoreo de los productos ','Operacciones',700.00,800.00,'Tiempo completo',NULL,1,'Activo','2026-03-15 22:52:05','2026-03-18');
/*!40000 ALTER TABLE `cargos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cat_estado_estudio`
--

DROP TABLE IF EXISTS `cat_estado_estudio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `cat_estado_estudio` (
  `id_estado` int(11) NOT NULL AUTO_INCREMENT,
  `codigo` varchar(50) NOT NULL,
  `descripcion` varchar(100) NOT NULL,
  PRIMARY KEY (`id_estado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cat_estado_estudio`
--

LOCK TABLES `cat_estado_estudio` WRITE;
/*!40000 ALTER TABLE `cat_estado_estudio` DISABLE KEYS */;
/*!40000 ALTER TABLE `cat_estado_estudio` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cat_estado_licencia`
--

DROP TABLE IF EXISTS `cat_estado_licencia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `cat_estado_licencia` (
  `id_estado` int(11) NOT NULL AUTO_INCREMENT,
  `codigo` varchar(50) NOT NULL,
  `descripcion` varchar(100) NOT NULL,
  PRIMARY KEY (`id_estado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cat_estado_licencia`
--

LOCK TABLES `cat_estado_licencia` WRITE;
/*!40000 ALTER TABLE `cat_estado_licencia` DISABLE KEYS */;
/*!40000 ALTER TABLE `cat_estado_licencia` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cat_estado_postulacion`
--

DROP TABLE IF EXISTS `cat_estado_postulacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `cat_estado_postulacion` (
  `id_estado` int(11) NOT NULL AUTO_INCREMENT,
  `codigo` varchar(50) NOT NULL,
  `descripcion` varchar(100) NOT NULL,
  PRIMARY KEY (`id_estado`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cat_estado_postulacion`
--

LOCK TABLES `cat_estado_postulacion` WRITE;
/*!40000 ALTER TABLE `cat_estado_postulacion` DISABLE KEYS */;
INSERT INTO `cat_estado_postulacion` VALUES
(1,'Recibido','Recibido'),
(2,'En revisiÃ³n','En revisiÃ³n'),
(3,'Entrevista tÃ©cnica','Entrevista tÃ©cnica'),
(4,'Entrevista RRHH','Entrevista RRHH'),
(5,'Oferta','Oferta'),
(6,'Contratado','Contratado'),
(7,'Rechazado','Rechazado'),
(8,'Descartado','Descartado');
/*!40000 ALTER TABLE `cat_estado_postulacion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cat_tipo_documento`
--

DROP TABLE IF EXISTS `cat_tipo_documento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `cat_tipo_documento` (
  `id_tipo` int(11) NOT NULL AUTO_INCREMENT,
  `codigo` varchar(50) NOT NULL,
  `descripcion` varchar(100) NOT NULL,
  PRIMARY KEY (`id_tipo`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cat_tipo_documento`
--

LOCK TABLES `cat_tipo_documento` WRITE;
/*!40000 ALTER TABLE `cat_tipo_documento` DISABLE KEYS */;
INSERT INTO `cat_tipo_documento` VALUES
(1,'CV','Curriculum Vitae');
/*!40000 ALTER TABLE `cat_tipo_documento` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `documentos`
--

DROP TABLE IF EXISTS `documentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `documentos` (
  `id_documento` int(11) NOT NULL AUTO_INCREMENT,
  `cedula` varchar(10) DEFAULT NULL,
  `id_postulacion` int(11) DEFAULT NULL,
  `id_tipo` int(11) DEFAULT NULL,
  `nombre_archivo` varchar(255) DEFAULT NULL,
  `ruta_archivo` varchar(500) DEFAULT NULL,
  `fecha_subida` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_documento`),
  KEY `id_tipo` (`id_tipo`),
  KEY `idx_postulacion` (`id_postulacion`),
  CONSTRAINT `1` FOREIGN KEY (`id_postulacion`) REFERENCES `postulaciones` (`id_postulacion`) ON DELETE CASCADE,
  CONSTRAINT `2` FOREIGN KEY (`id_tipo`) REFERENCES `cat_tipo_documento` (`id_tipo`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `documentos`
--

LOCK TABLES `documentos` WRITE;
/*!40000 ALTER TABLE `documentos` DISABLE KEYS */;
INSERT INTO `documentos` VALUES
(1,'9999999999',NULL,1,'curriculum.pdf','uploads/curriculum/curriculum.pdf','2026-03-16 00:47:13'),
(2,'1234567890',NULL,1,'CV_Maria_Gonzalez.pdf','uploads/curriculum/CV_Maria_Gonzalez.pdf','2026-03-16 00:49:07'),
(3,'1114587542',NULL,1,'1114587542_Saul_Segovia.pdf','uploads/curriculum/1114587542_Saul_Segovia.pdf','2026-03-16 01:03:20');
/*!40000 ALTER TABLE `documentos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `estudios`
--

DROP TABLE IF EXISTS `estudios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `estudios` (
  `id_estudio` int(11) NOT NULL AUTO_INCREMENT,
  `nivel_estudio` varchar(100) NOT NULL,
  PRIMARY KEY (`id_estudio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `estudios`
--

LOCK TABLES `estudios` WRITE;
/*!40000 ALTER TABLE `estudios` DISABLE KEYS */;
/*!40000 ALTER TABLE `estudios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `experiencias`
--

DROP TABLE IF EXISTS `experiencias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `experiencias` (
  `id_experiencia` int(11) NOT NULL AUTO_INCREMENT,
  `cedula` varchar(10) NOT NULL,
  `empresa` varchar(100) NOT NULL,
  `cargo` varchar(100) NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date DEFAULT NULL,
  `actual` tinyint(1) DEFAULT 0,
  `descripcion` text DEFAULT NULL,
  PRIMARY KEY (`id_experiencia`),
  KEY `idx_cedula` (`cedula`),
  CONSTRAINT `1` FOREIGN KEY (`cedula`) REFERENCES `candidatos` (`cedula`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `experiencias`
--

LOCK TABLES `experiencias` WRITE;
/*!40000 ALTER TABLE `experiencias` DISABLE KEYS */;
INSERT INTO `experiencias` VALUES
(4,'9999999999','Tech Corp','Desarrollador Senior','2020-01-15','2022-12-31',0,'Trabajo en backend con Python'),
(5,'9999999999','Digital Solutions','Desarrollador Full Stack','2022-02-01','2023-11-30',0,'Desarrollo web completo'),
(6,'9999999999','StartUp XYZ','Tech Lead','2023-12-01',NULL,0,'Liderazgo de equipo técnico'),
(7,'1234567890','Ministerio de Salud','Médica General','2018-06-01','2021-08-31',0,'Atención a pacientes, diagnósticos, prescripción de tratamientos'),
(8,'1234567890','Hospital Metropolitano','Médica Especialista en Cardiología','2021-09-15',NULL,0,'Diagnóstico y tratamiento de enfermedades cardiovasculares, cirugías menores'),
(9,'1234567890','Clínica Familiar Visión','Médica Consultor','2023-01-10',NULL,0,'Consultoría medica, supervisión de equipo de salud'),
(10,'1114587542','lkjljkljk','ljkljkljkl','2025-02-15','2026-03-08',0,'ljkliououo'),
(11,'1114587542','rtytry','ytruytiuy','2026-03-01','2026-03-02',0,'uyi7898o98po'),
(12,'1114587542','dsadasdsa','sdfdgdfg','2024-01-15','2025-05-15',0,'ghgfhfghhj');
/*!40000 ALTER TABLE `experiencias` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `historial`
--

DROP TABLE IF EXISTS `historial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `historial` (
  `id_historial` int(11) NOT NULL AUTO_INCREMENT,
  `id_postulacion` int(11) NOT NULL,
  `estado` varchar(50) DEFAULT NULL,
  `fecha_registro` timestamp NULL DEFAULT current_timestamp(),
  `descripcion` text DEFAULT NULL,
  PRIMARY KEY (`id_historial`),
  KEY `idx_postulacion` (`id_postulacion`),
  CONSTRAINT `1` FOREIGN KEY (`id_postulacion`) REFERENCES `postulaciones` (`id_postulacion`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `historial`
--

LOCK TABLES `historial` WRITE;
/*!40000 ALTER TABLE `historial` DISABLE KEYS */;
/*!40000 ALTER TABLE `historial` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `licencias`
--

DROP TABLE IF EXISTS `licencias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `licencias` (
  `id_licencia` int(11) NOT NULL AUTO_INCREMENT,
  `cedula` varchar(10) NOT NULL,
  `tipo` varchar(100) NOT NULL,
  `fecha_vencimiento` date DEFAULT NULL,
  `estado` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_licencia`),
  KEY `idx_cedula` (`cedula`),
  CONSTRAINT `1` FOREIGN KEY (`cedula`) REFERENCES `candidatos` (`cedula`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `licencias`
--

LOCK TABLES `licencias` WRITE;
/*!40000 ALTER TABLE `licencias` DISABLE KEYS */;
/*!40000 ALTER TABLE `licencias` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `postulaciones`
--

DROP TABLE IF EXISTS `postulaciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `postulaciones` (
  `id_postulacion` int(11) NOT NULL AUTO_INCREMENT,
  `cedula` varchar(10) NOT NULL,
  `id_cargo` int(11) NOT NULL,
  `fecha_postulacion` timestamp NULL DEFAULT current_timestamp(),
  `estado` varchar(50) DEFAULT 'Recibido',
  `fuente_reclutamiento` varchar(100) DEFAULT NULL,
  `notas` text DEFAULT NULL,
  `puntaje_evaluacion` int(11) DEFAULT NULL,
  `fecha_actualizacion` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_postulacion`),
  UNIQUE KEY `uk_candidato_cargo` (`cedula`,`id_cargo`),
  KEY `idx_cedula` (`cedula`),
  KEY `idx_cargo` (`id_cargo`),
  KEY `idx_estado` (`estado`),
  CONSTRAINT `1` FOREIGN KEY (`cedula`) REFERENCES `candidatos` (`cedula`) ON DELETE CASCADE,
  CONSTRAINT `2` FOREIGN KEY (`id_cargo`) REFERENCES `cargos` (`id_cargo`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `postulaciones`
--

LOCK TABLES `postulaciones` WRITE;
/*!40000 ALTER TABLE `postulaciones` DISABLE KEYS */;
INSERT INTO `postulaciones` VALUES
(1,'1114587542',5,'2026-03-16 01:04:49','Rechazado',NULL,NULL,NULL,'2026-03-19 01:40:11'),
(2,'0904258740',5,'2026-03-19 00:17:47','En revisión',NULL,NULL,NULL,'2026-03-19 01:22:10');
/*!40000 ALTER TABLE `postulaciones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `referencias_personales`
--

DROP TABLE IF EXISTS `referencias_personales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `referencias_personales` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cedula` varchar(10) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `empresa` varchar(150) DEFAULT NULL,
  `cargo` varchar(100) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `relacion` varchar(50) DEFAULT NULL,
  `descripcion` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_cedula` (`cedula`),
  CONSTRAINT `1` FOREIGN KEY (`cedula`) REFERENCES `candidatos` (`cedula`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `referencias_personales`
--

LOCK TABLES `referencias_personales` WRITE;
/*!40000 ALTER TABLE `referencias_personales` DISABLE KEYS */;
INSERT INTO `referencias_personales` VALUES
(4,'9999999999','Carlos López','Empresa A','Gerente','0987654321','carlos@example.com',NULL,NULL),
(5,'9999999999','María García','Empresa B','Supervisora','0987654322','maria@example.com',NULL,NULL),
(6,'9999999999','Pedro Martínez','Empresa C','Jefe de Proyecto','0987654323','pedro@example.com',NULL,NULL),
(7,'1234567890','Dr. Carlos Ruiz','Hospital San Francisco','Jefe de Métodos','0987654321','carlos.ruiz@hsf.com',NULL,NULL),
(8,'1234567890','Ing. Patricia López','TechSolutions Inc','Directora de IT','0987654322','patricia@techsolutions.com',NULL,NULL),
(9,'1234567890','Lic. Juan Morales','Consultoría ABC','Socio Consultor','0987654323','juan.morales@consultoría.com',NULL,NULL),
(10,'1114587542','Caila','fdsfsdf','fdsfsdf','0997474028','ctrlv593@gmail.com',NULL,NULL),
(11,'1114587542','hrtyry','hghjj','lkjljl','0997474028','ctrlv593@gmail.com',NULL,NULL),
(12,'1114587542','ytyruyu','hgjhgjk','hlkjlj','lkjlkklj','lkj@gmail.com',NULL,NULL);
/*!40000 ALTER TABLE `referencias_personales` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `id_rol` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `descripcion` text DEFAULT NULL,
  PRIMARY KEY (`id_rol`),
  UNIQUE KEY `nombre` (`nombre`),
  KEY `idx_nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=153 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES
(1,'admin','Administrador del sistema - Acceso completo'),
(2,'reclutador','Reclutador - GestiÃ³n de cargos, candidatos y postulaciones'),
(3,'gerente','Gerente de RRHH - VisualizaciÃ³n de reportes'),
(4,'candidato','Candidato - Registro y seguimiento de postulaciones');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sucursales`
--

DROP TABLE IF EXISTS `sucursales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `sucursales` (
  `id_sucursal` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `ciudad` varchar(100) DEFAULT NULL,
  `direccion` text DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `activa` tinyint(1) DEFAULT 1,
  `fecha_creacion` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_sucursal`),
  UNIQUE KEY `nombre` (`nombre`),
  KEY `idx_nombre` (`nombre`),
  KEY `idx_activa` (`activa`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sucursales`
--

LOCK TABLES `sucursales` WRITE;
/*!40000 ALTER TABLE `sucursales` DISABLE KEYS */;
INSERT INTO `sucursales` VALUES
(1,'El Inca','Quito',NULL,NULL,1,'2026-03-15 22:25:08'),
(2,'Calderon','Quito',NULL,NULL,1,'2026-03-15 22:25:08'),
(3,'Mitad del mundo','Quito',NULL,NULL,1,'2026-03-15 22:25:08'),
(4,'Occidental','Quito',NULL,NULL,1,'2026-03-15 22:25:08'),
(5,'Tumbaco','Quito',NULL,NULL,1,'2026-03-15 22:25:08');
/*!40000 ALTER TABLE `sucursales` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `telefonos`
--

DROP TABLE IF EXISTS `telefonos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `telefonos` (
  `id_telefono` int(11) NOT NULL AUTO_INCREMENT,
  `numero` varchar(20) NOT NULL,
  `tipo` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_telefono`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `telefonos`
--

LOCK TABLES `telefonos` WRITE;
/*!40000 ALTER TABLE `telefonos` DISABLE KEYS */;
/*!40000 ALTER TABLE `telefonos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id_usuario` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_usuario` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `rol_id` int(11) NOT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `ultimo_acceso` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `nombre_usuario` (`nombre_usuario`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_nombre_usuario` (`nombre_usuario`),
  KEY `idx_email` (`email`),
  KEY `idx_rol` (`rol_id`),
  CONSTRAINT `1` FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id_rol`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES
(1,'admin','admin@reclutamiento.com','pbkdf2:sha256:600000$bkBvX3xY$9e7d8b9c8c8d8b8d8b8d8b8d8b8d8b8d8b8d8b8d',1,1,'2026-03-15 18:12:34',NULL),
(2,'Vladimir','ctrlv593@gmail.com','pbkdf2:sha256:1000000$dqBiWyvCj8vr7ncI$6fa59f8638d605277406c615a9b527abab6d74b3f5d3b936397113291fc81432',4,1,'2026-03-15 18:18:22',NULL),
(3,'vbecerra_admin','krisvladbec@gmail.com','pbkdf2:sha256:1000000$llfYLG8N1jrBwGYJ$2bcfaa7ab362db62d696241cd9a46973f6f18f7286790f30687a8a7714262abf',1,1,'2026-03-15 19:53:58',NULL),
(4,'juanperez','juan.perez@correo.com','pbkdf2:sha256:1000000$xlaUSkt2RhM3Z8eK$dd64795d4eb818138c855efb2919d60832a09818d7c02257df5e30644d50bd1f',4,1,'2026-03-15 19:53:59',NULL),
(5,'ChisPat','Chrisp@hotmail.com','pbkdf2:sha256:1000000$f3nN6Hm7UB2qY9Hb$65d0f803edb093371c64f26c5f17b592f55dad321f388cf0d7de2eac32287c92',4,1,'2026-03-15 23:07:42',NULL),
(6,'papeles','papeles@gmail.com','pbkdf2:sha256:1000000$BQUOKhW5qVmTC86U$65dd6a9b54cd4503896bb082edf96ba32f0f4c730ca93e417832bad1a9ee4706',4,1,'2026-03-16 00:04:56',NULL),
(7,'prueba3','prueba3@gmail.com','pbkdf2:sha256:1000000$dWpeV5tSsuWFAtLR$9a4d31bebbe415b424f957628984d5b03cacfe62390d2b762d9c3f7c72acff7c',4,1,'2026-03-16 00:22:45',NULL),
(8,'maria.gonzalez','maria.gonzalez@gmail.com','pbkdf2:sha256:1000000$2LsoA1wEiNbO83qQ$88260d48e33f2816926c7911390072acf3c9859703afe0870ba30303bbf7c56f',4,1,'2026-03-16 00:49:07',NULL),
(9,'canal','canal@hotmail.com','pbkdf2:sha256:1000000$SRBF7yFs3NOvGUe6$f797086b2a690788c099311dda8d9cf558ae727a63977d9a575b9f98a3d375d9',4,1,'2026-03-19 00:49:38',NULL);
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'reclutamiento'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2026-03-21 13:24:11
