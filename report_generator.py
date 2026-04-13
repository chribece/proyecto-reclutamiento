from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.colors import HexColor
from io import BytesIO
from datetime import datetime
from database import db
from config import Config

class ReportGenerator:
    """Generador de reportes PDF mejorado"""
    
    @staticmethod
    def _get_header_elements():
        """Elementos del encabezado corporativo"""
        styles = getSampleStyleSheet()
        
        # Título principal
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=HexColor(Config.COLORS['dark']),
            spaceAfter=10,
            alignment=TA_CENTER
        )
        
        # Subtítulo
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor(Config.COLORS['secondary']),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        return title_style, subtitle_style
    
    @staticmethod
    def _get_table_style():
        """Estilo uniforme para todas las tablas"""
        return TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), HexColor(Config.COLORS['dark'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Filas de datos
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            
            # Filas alternas
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('BACKGROUND', (0, 2), (-1, -1), HexColor(Config.COLORS['light'])),
        ])
    
    @staticmethod
    def generate_candidatos_por_vacante_report(cargo_id=None, cargo_nombre="Todas las Vacantes"):
        """
        Genera reporte PDF de candidatos con información esencial
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        styles = getSampleStyleSheet()
        title_style, subtitle_style = ReportGenerator._get_header_elements()
        
        # ============ ENCABEZADO ============
        elements.append(Paragraph("SISTEMA DE RECLUTAMIENTO", title_style))
        elements.append(Paragraph(f"Reporte de Candidatos - {cargo_nombre}", subtitle_style))
        elements.append(Paragraph(
            f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            styles['Normal']
        ))
        elements.append(Spacer(1, 0.3*inch))
        
        # ============ OBTENER DATOS ============
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            if cargo_id:
                # Candidatos postulados a un cargo específico
                cursor.execute('''
                    SELECT DISTINCT 
                        c.cedula,
                        c.nombre,
                        c.apellido,
                        c.email,
                        c.telefono,
                        c.nivel_educativo,
                        c.experiencia_anos,
                        c.direccion_domicilio,
                        c.disponibilidad,
                        cg.nombre as cargo_nombre,
                        p.estado,
                        p.fecha_postulacion
                    FROM candidatos c
                    INNER JOIN postulaciones p ON c.cedula = p.cedula
                    INNER JOIN cargos cg ON p.id_cargo = cg.id_cargo
                    WHERE p.id_cargo = %s AND c.activo = TRUE
                    ORDER BY p.fecha_postulacion DESC
                ''', (cargo_id,))
            else:
                # Todos los candidatos con postulaciones
                cursor.execute('''
                    SELECT DISTINCT 
                        c.cedula,
                        c.nombre,
                        c.apellido,
                        c.email,
                        c.nivel_educativo,
                        c.experiencia_anos,
                        c.direccion_domicilio,
                        c.disponibilidad,
                        cg.nombre as cargo_nombre,
                        p.estado,
                        p.fecha_postulacion
                    FROM candidatos c
                    INNER JOIN postulaciones p ON c.cedula = p.cedula
                    INNER JOIN cargos cg ON p.id_cargo = cg.id_cargo
                    WHERE c.activo = TRUE
                    ORDER BY p.fecha_postulacion DESC
                ''')
            
            candidatos = cursor.fetchall()
        
        # ============ TABLA DE CANDIDATOS ============
        # Columnas esenciales (solo información relevante)
        headers = ['N°', 'Candidato', 'Cargo', 'Estado', 'Educación', 'Exp.', 'Disponibilidad']
        
        data = [headers]
        for i, c in enumerate(candidatos, 1):
            # Nombre completo combinado
            nombre_completo = f"{c['nombre']} {c['apellido']}"
            if len(nombre_completo) > 25:
                nombre_completo = nombre_completo[:22] + "..."
            
            # Cargo (truncar si es muy largo)
            cargo = c['cargo_nombre'] if c['cargo_nombre'] else 'N/A'
            if len(cargo) > 20:
                cargo = cargo[:17] + "..."
            
            # Estado con formato
            estado = c['estado'] if c['estado'] else 'Recibido'
            
            # Educación
            educacion = c['nivel_educativo'] if c['nivel_educativo'] else 'No especificado'
            if len(educacion) > 15:
                educacion = educacion[:12] + "..."
            
            # Experiencia
            experiencia = f"{c['experiencia_anos']} años" if c['experiencia_anos'] else '0 años'
            
            # Disponibilidad
            disponibilidad = c['disponibilidad'] if c['disponibilidad'] else 'N/A'
            if len(disponibilidad) > 12:
                disponibilidad = disponibilidad[:9] + "..."
            
            data.append([
                str(i),
                nombre_completo,
                cargo,
                estado,
                educacion,
                experiencia,
                disponibilidad
            ])
        
        # Crear tabla con anchos de columna definidos
        table = Table(data, colWidths=[0.5*cm, 3.5*cm, 3.5*cm, 2*cm, 2.5*cm, 1.5*cm, 2.5*cm])
        table.setStyle(ReportGenerator._get_table_style())
        elements.append(table)
        
        elements.append(Spacer(1, 0.5*inch))
        
        # ============ RESUMEN ESTADÍSTICO ============
        elements.append(Paragraph("RESUMEN ESTADÍSTICO", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Calcular estadísticas
        total_candidatos = len(candidatos)
        
        # Experiencia promedio
        exp_total = sum(c['experiencia_anos'] or 0 for c in candidatos)
        exp_promedio = round(exp_total / total_candidatos, 1) if total_candidatos > 0 else 0
        
        # Contar por nivel educativo
        niveles = {}
        for c in candidatos:
            nivel = c['nivel_educativo'] if c['nivel_educativo'] else 'No especificado'
            niveles[nivel] = niveles.get(nivel, 0) + 1
        
        # Contar por estado de postulación
        estados = {}
        for c in candidatos:
            estado = c['estado'] if c['estado'] else 'Recibido'
            estados[estado] = estados.get(estado, 0) + 1
        
        # Tabla de estadísticas
        stats_data = [
            ['Métrica', 'Valor'],
            ['Total de Candidatos', str(total_candidatos)],
            ['Experiencia Promedio', f'{exp_promedio} años'],
            ['Con Educación Superior', str(niveles.get('Universitario', 0) + niveles.get('Posgrado', 0))],
            ['Con Educación Técnica', str(niveles.get('Técnico', 0))],
            ['Disponibilidad Inmediata', str(sum(1 for c in candidatos if c['disponibilidad'] == 'Inmediata'))],
        ]
        
        stats_table = Table(stats_data, colWidths=[4*cm, 3*cm])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor(Config.COLORS['primary'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ]))
        elements.append(stats_table)
        
        elements.append(Spacer(1, 0.3*inch))
        
        # ============ PIE DE PÁGINA ============
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("Documento generado automáticamente por el Sistema de Reclutamiento", footer_style))
        elements.append(Paragraph(f"© {datetime.now().year} - Todos los derechos reservados", footer_style))
        
        # ============ GENERAR PDF ============
        doc.build(elements)
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def generate_estadisticas_postulaciones_report(fecha_inicio=None, fecha_fin=None):
        """
        Genera reporte PDF de estadísticas de postulaciones
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        
        elements = []
        styles = getSampleStyleSheet()
        title_style, subtitle_style = ReportGenerator._get_header_elements()
        
        # Encabezado
        elements.append(Paragraph("SISTEMA DE RECLUTAMIENTO", title_style))
        elements.append(Paragraph("Reporte de Estadísticas de Postulaciones", subtitle_style))
        
        periodo = ""
        if fecha_inicio and fecha_fin:
            periodo = f"Período: {fecha_inicio} al {fecha_fin}"
        else:
            periodo = "Período: Todo el historial"
        elements.append(Paragraph(periodo, styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Obtener datos
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total de postulaciones
            cursor.execute('SELECT COUNT(*) as total FROM postulaciones')
            total = cursor.fetchone()['total']
            
            # Por estado
            cursor.execute('''
                SELECT estado, COUNT(*) as cantidad 
                FROM postulaciones 
                GROUP BY estado 
                ORDER BY cantidad DESC
            ''')
            por_estado = cursor.fetchall()
            
            # Por cargo (top 10)
            cursor.execute('''
                SELECT cg.nombre, COUNT(p.id_postulacion) as cantidad 
                FROM postulaciones p
                INNER JOIN cargos cg ON p.id_cargo = cg.id_cargo
                GROUP BY cg.nombre 
                ORDER BY cantidad DESC 
                LIMIT 10
            ''')
            por_cargo = cursor.fetchall()
            
            # Tasa de conversión
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN estado = 'Contratado' THEN 1 ELSE 0 END) as contratados,
                    COUNT(*) as total
                FROM postulaciones
            ''')
            conversion = cursor.fetchone()
            tasa = round((conversion['contratados'] / conversion['total'] * 100), 2) if conversion['total'] > 0 else 0
        
        # Tabla: Por Estado
        elements.append(Paragraph("POSTULACIONES POR ESTADO", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        estado_data = [['Estado', 'Cantidad', 'Porcentaje']]
        for row in por_estado:
            porcentaje = round((row['cantidad'] / total * 100), 1) if total > 0 else 0
            estado_data.append([row['estado'], str(row['cantidad']), f'{porcentaje}%'])
        
        estado_table = Table(estado_data, colWidths=[4*cm, 2*cm, 2*cm])
        estado_table.setStyle(ReportGenerator._get_table_style())
        elements.append(estado_table)
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Tabla: Top Cargos
        elements.append(Paragraph("TOP 10 CARGOS CON MÁS POSTULACIONES", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        cargo_data = [['Cargo', 'Postulaciones']]
        for row in por_cargo:
            cargo_nombre = row['nombre'][:40] + "..." if len(row['nombre']) > 40 else row['nombre']
            cargo_data.append([cargo_nombre, str(row['cantidad'])])
        
        cargo_table = Table(cargo_data, colWidths=[5*cm, 2*cm])
        cargo_table.setStyle(ReportGenerator._get_table_style())
        elements.append(cargo_table)
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Métricas clave
        elements.append(Paragraph("MÉTRICAS CLAVE", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        metricas_data = [
            ['Métrica', 'Valor'],
            ['Total de Postulaciones', str(total)],
            ['Tasa de Contratación', f'{tasa}%'],
            ['Estados Activos', str(len(por_estado))],
        ]
        
        metricas_table = Table(metricas_data, colWidths=[4*cm, 3*cm])
        metricas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor(Config.COLORS['primary'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(metricas_table)
        
        # Footer
        elements.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
        elements.append(Paragraph("Documento generado automáticamente por el Sistema de Reclutamiento", footer_style))
        
        doc.build(elements)
        buffer.seek(0)
        
        return buffer


# Funciones helper para app.py
def create_pdf_response(buffer, filename):
    """Crea respuesta Flask con PDF"""
    from flask import make_response
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


report_generator = ReportGenerator()