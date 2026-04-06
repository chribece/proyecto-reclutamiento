// Utilidades generales
const App = {
    // Confirmación para eliminaciones
    confirmDelete: function(message = '¿Está seguro de eliminar este elemento?') {
        return confirm(message);
    },
    
    // Formatear fechas relativas
    timeAgo: function(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);
        
        let interval = seconds / 31536000;
        if (interval > 1) return Math.floor(interval) + " años";
        interval = seconds / 2592000;
        if (interval > 1) return Math.floor(interval) + " meses";
        interval = seconds / 86400;
        if (interval > 1) return Math.floor(interval) + " días";
        interval = seconds / 3600;
        if (interval > 1) return Math.floor(interval) + " horas";
        interval = seconds / 60;
        if (interval > 1) return Math.floor(interval) + " minutos";
        return "Justo ahora";
    },
    
    // Inicializar tooltips y componentes
    init: function() {
        this.initFlashMessages();
        this.initConfirmations();
        this.initAutoRefresh();
    },
    
    initFlashMessages: function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            setTimeout(() => {
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(100%)';
                setTimeout(() => alert.remove(), 300);
            }, 5000);
        });
    },
    
    initConfirmations: function() {
        document.querySelectorAll('[data-confirm]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                if (!confirm(btn.dataset.confirm)) {
                    e.preventDefault();
                }
            });
        });
    },
    
    initAutoRefresh: function() {
        // Actualizar timestamps cada minuto
        setInterval(() => {
            document.querySelectorAll('[data-timestamp]').forEach(el => {
                el.textContent = this.timeAgo(el.dataset.timestamp);
            });
        }, 60000);
    },
    
    // Cambiar estado de postulación vía AJAX
    cambiarEstado: async function(postulacionId, nuevoEstado) {
        try {
            const formData = new FormData();
            formData.append('estado', nuevoEstado);
            
            const response = await fetch(`/postulaciones/${postulacionId}/cambiar-estado`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                window.location.reload();
            } else {
                alert('Error al cambiar el estado');
            }
        } catch (error) {
            console.error('Error:', error);
        }
    },
    
    // Filtrado dinámico de tablas
    filtrarTabla: function(inputId, tablaId) {
        const input = document.getElementById(inputId);
        const tabla = document.getElementById(tablaId);
        
        if (!input || !tabla) return;
        
        input.addEventListener('input', (e) => {
            const filtro = e.target.value.toLowerCase();
            const filas = tabla.querySelectorAll('tbody tr');
            
            filas.forEach(fila => {
                const texto = fila.textContent.toLowerCase();
                fila.style.display = texto.includes(filtro) ? '' : 'none';
            });
        });
    }
};

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    App.init();
    
    // Inicializar filtros si existen
    App.filtrarTabla('busqueda-candidatos', 'tabla-candidatos');
    App.filtrarTabla('busqueda-cargos', 'tabla-cargos');
});

// Exportar para uso global
window.App = App;