-- =====================================================
-- 1. HABILITAR CLAVES FORÁNEAS
-- =====================================================
PRAGMA foreign_keys = ON;

-- =====================================================
-- 2. TABLA USUARIO (ACTUALIZADA)
-- =====================================================
CREATE TABLE Usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombres TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    nombre TEXT NOT NULL,   -- Nombre completo (para compatibilidad con el frontend)
    email TEXT UNIQUE NOT NULL,
    telefono TEXT,
    contrasena_hash TEXT NOT NULL,
    rol TEXT NOT NULL CHECK(rol IN ('residente','administrador')),
    nacionalidad TEXT NOT NULL CHECK(nacionalidad IN ('peruana','extranjero')) DEFAULT 'peruana',
    tipo_documento TEXT NOT NULL CHECK(tipo_documento IN ('DNI','Carnet de Extranjería')),
    numero_documento TEXT NOT NULL UNIQUE,
    fecha_nacimiento DATE NOT NULL,
    activo INTEGER DEFAULT 1   -- 1 = activo, 0 = pendiente de aprobación
);

-- =====================================================
-- 3. TABLA RESIDENTE
-- =====================================================
CREATE TABLE Residente (
    id_residente INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL UNIQUE,
    nro_departamento TEXT NOT NULL,
    estado_financiero TEXT NOT NULL
        CHECK(estado_financiero IN ('al_dia','moroso')),
    fecha_ingreso DATE NOT NULL,

    FOREIGN KEY(id_usuario)
        REFERENCES Usuario(id_usuario)
);

-- =====================================================
-- 4. TABLA ADMINISTRADOR
-- =====================================================
CREATE TABLE Administrador (
    id_administrador INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL UNIQUE,
    cargo TEXT NOT NULL,
    permisos TEXT,

    FOREIGN KEY(id_usuario)
        REFERENCES Usuario(id_usuario)
);

-- =====================================================
-- 5. TABLA CUOTA_MANTENIMIENTO
-- =====================================================
CREATE TABLE Cuota_Mantenimiento (
    id_cuota INTEGER PRIMARY KEY AUTOINCREMENT,
    id_residente INTEGER NOT NULL,
    periodo TEXT NOT NULL,
    monto REAL NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    estado TEXT NOT NULL
        CHECK(estado IN ('pendiente','pagado','vencido')),

    FOREIGN KEY(id_residente)
        REFERENCES Residente(id_residente)
);

-- =====================================================
-- 6. TABLA PAGO
-- =====================================================
CREATE TABLE Pago (
    id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cuota INTEGER NOT NULL,
    id_residente INTEGER NOT NULL,
    monto REAL NOT NULL,
    fecha_pago DATE NOT NULL,
    numero_operacion TEXT,
    comprobante_url TEXT,
    estado TEXT NOT NULL
        CHECK(estado IN ('pendiente','aprobado','rechazado')),
    fecha_validacion DATETIME,
    observacion_validacion TEXT,
    id_admin_validador INTEGER,

    FOREIGN KEY(id_cuota)
        REFERENCES Cuota_Mantenimiento(id_cuota),

    FOREIGN KEY(id_residente)
        REFERENCES Residente(id_residente),

    FOREIGN KEY(id_admin_validador)
        REFERENCES Administrador(id_administrador)
);

-- =====================================================
-- 7. TABLA INCIDENCIA
-- =====================================================
CREATE TABLE Incidencia (
    id_incidencia INTEGER PRIMARY KEY AUTOINCREMENT,
    id_residente INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    categoria TEXT NOT NULL
        CHECK(categoria IN ('mantenimiento','seguridad','servicios','otros')),
    prioridad TEXT NOT NULL
        CHECK(prioridad IN ('baja','media','alta')),
    estado TEXT NOT NULL
        CHECK(estado IN ('nuevo','asignado','en_progreso','resuelto','cerrado')),
    fecha_creacion DATETIME NOT NULL,
    fecha_cierre DATETIME,
    evidencia_url TEXT,
    id_admin_asignado INTEGER,
    clasificacion_ia TEXT,

    FOREIGN KEY(id_residente)
        REFERENCES Residente(id_residente),

    FOREIGN KEY(id_admin_asignado)
        REFERENCES Administrador(id_administrador)
);

-- =====================================================
-- 8. TABLA INCIDENCIA_SEGUIMIENTO
-- =====================================================
CREATE TABLE Incidencia_Seguimiento (
    id_seguimiento INTEGER PRIMARY KEY AUTOINCREMENT,
    id_incidencia INTEGER NOT NULL,
    id_usuario INTEGER NOT NULL,
    comentario TEXT NOT NULL,
    estado_anterior TEXT NOT NULL,
    estado_nuevo TEXT NOT NULL,
    fecha_registro DATETIME NOT NULL,

    FOREIGN KEY(id_incidencia)
        REFERENCES Incidencia(id_incidencia),

    FOREIGN KEY(id_usuario)
        REFERENCES Usuario(id_usuario)
);

-- =====================================================
-- 9. TABLA AREA_COMUN
-- =====================================================
CREATE TABLE Area_Comun (
    id_area INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    capacidad INTEGER NOT NULL,
    horario_inicio TIME NOT NULL,
    horario_fin TIME NOT NULL,
    activo INTEGER DEFAULT 1
);

-- =====================================================
-- 10. TABLA RESERVA
-- =====================================================
CREATE TABLE Reserva (
    id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
    id_residente INTEGER NOT NULL,
    id_area INTEGER NOT NULL,
    fecha_reserva DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    estado TEXT NOT NULL
        CHECK(estado IN ('pendiente','confirmada','cancelada')),
    fecha_solicitud DATETIME NOT NULL,

    FOREIGN KEY(id_residente)
        REFERENCES Residente(id_residente),

    FOREIGN KEY(id_area)
        REFERENCES Area_Comun(id_area)
);

-- =====================================================
-- 11. TABLA COMUNICACION
-- =====================================================
CREATE TABLE Comunicacion (
    id_comunicacion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_admin_remitente INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    mensaje TEXT NOT NULL,
    fecha_envio DATETIME NOT NULL,
    tipo TEXT NOT NULL
        CHECK(tipo IN ('informativo','urgente','recordatorio')),

    FOREIGN KEY(id_admin_remitente)
        REFERENCES Administrador(id_administrador)
);

-- =====================================================
-- 12. TABLA COMUNICACION_DESTINATARIO
-- =====================================================
CREATE TABLE Comunicacion_Destinatario (
    id_destinatario INTEGER PRIMARY KEY AUTOINCREMENT,
    id_comunicacion INTEGER NOT NULL,
    id_residente INTEGER NOT NULL,

    FOREIGN KEY(id_comunicacion)
        REFERENCES Comunicacion(id_comunicacion),

    FOREIGN KEY(id_residente)
        REFERENCES Residente(id_residente)
);

-- =====================================================
-- 13. TABLA NOTIFICACION
-- =====================================================
CREATE TABLE Notificacion (
    id_notificacion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_residente INTEGER NOT NULL,
    id_comunicacion INTEGER,
    tipo TEXT NOT NULL,
    url_accion TEXT,
    leido INTEGER DEFAULT 0,
    fecha_lectura DATETIME,

    FOREIGN KEY(id_residente)
        REFERENCES Residente(id_residente),

    FOREIGN KEY(id_comunicacion)
        REFERENCES Comunicacion(id_comunicacion)
);

-- =====================================================
-- 14. TABLA DOCUMENTO
-- =====================================================
CREATE TABLE Documento (
    id_documento INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    archivo_url TEXT NOT NULL,
    fecha_publicacion DATETIME NOT NULL,
    id_administrador INTEGER NOT NULL,

    FOREIGN KEY(id_administrador)
        REFERENCES Administrador(id_administrador)
);

-- =====================================================
-- 15. TABLA LOG_AUDITORIA
-- =====================================================
CREATE TABLE Log_Auditoria (
    id_log INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    accion TEXT NOT NULL,
    entidad_afectada TEXT NOT NULL,
    id_registro_afectado INTEGER NOT NULL,
    fecha_hora DATETIME NOT NULL,
    ip_origen TEXT,
    navegador TEXT,
    detalle TEXT,

    FOREIGN KEY(id_usuario)
        REFERENCES Usuario(id_usuario)
);

-- =====================================================
-- 16. NUEVA TABLA: INVITACION
-- =====================================================
CREATE TABLE Invitacion (
    id_invitacion INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    dpto_destino TEXT NOT NULL,
    usado INTEGER DEFAULT 0,
    id_admin_creador INTEGER NOT NULL,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(id_admin_creador)
        REFERENCES Administrador(id_administrador)
);

-- =====================================================
-- 17. NUEVA TABLA: SOLICITUD_REGISTRO
-- =====================================================
CREATE TABLE Solicitud_Registro (
    id_solicitud INTEGER PRIMARY KEY AUTOINCREMENT,
    nombres TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    email TEXT NOT NULL,
    telefono TEXT,
    dpto_solicitado TEXT,
    estado TEXT NOT NULL CHECK(estado IN ('pendiente','aprobado','rechazado')) DEFAULT 'pendiente',
    fecha_solicitud DATETIME DEFAULT CURRENT_TIMESTAMP,
    motivo_rechazo TEXT,
    id_admin_procesa INTEGER,

    FOREIGN KEY(id_admin_procesa)
        REFERENCES Administrador(id_administrador)
);

-- =====================================================
-- 18. ÍNDICES PARA MEJORAR RENDIMIENTO
-- =====================================================
CREATE INDEX IDX_USUARIO_EMAIL ON Usuario(email);
CREATE INDEX IDX_USUARIO_DOCUMENTO ON Usuario(numero_documento);
CREATE INDEX IDX_CUOTA_RESIDENTE ON Cuota_Mantenimiento(id_residente);
CREATE INDEX IDX_PAGO_RESIDENTE ON Pago(id_residente);
CREATE INDEX IDX_INCIDENCIA_RESIDENTE ON Incidencia(id_residente);
CREATE INDEX IDX_RESERVA_RESIDENTE ON Reserva(id_residente);
CREATE INDEX IDX_NOTIFICACION_RESIDENTE ON Notificacion(id_residente);
CREATE INDEX IDX_LOG_USUARIO ON Log_Auditoria(id_usuario);
CREATE INDEX IDX_INVITACION_CODIGO ON Invitacion(codigo);
CREATE INDEX IDX_SOLICITUD_EMAIL ON Solicitud_Registro(email);