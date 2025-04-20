document.addEventListener('DOMContentLoaded', function() {
    // Manejo del dropdown del dashboard
    const dashboardDropdown = document.getElementById('dashboardDropdown');
    const dashboardDropdownContent = document.getElementById('dashboardDropdownContent');
    
    if (dashboardDropdown && dashboardDropdownContent) {
        // Verificar si hay algún elemento activo en el dropdown
        const activeItem = dashboardDropdownContent.querySelector('.active');
        
        // Si hay un elemento activo, mostrar el dropdown
        if (activeItem) {
            dashboardDropdownContent.classList.add('show');
            dashboardDropdown.querySelector('.fa-caret-down').style.transform = 'rotate(180deg)';
        }
        
        // Toggle del dropdown al hacer clic
        dashboardDropdown.addEventListener('click', function() {
            dashboardDropdownContent.classList.toggle('show');
            
            // Rotar el ícono de caret
            const caretIcon = this.querySelector('.fa-caret-down');
            if (dashboardDropdownContent.classList.contains('show')) {
                caretIcon.style.transform = 'rotate(180deg)';
            } else {
                caretIcon.style.transform = 'rotate(0)';
            }
        });
    }
    
    // Cerrar dropdown al hacer clic fuera de él
    document.addEventListener('click', function(event) {
        if (dashboardDropdown && dashboardDropdownContent && !dashboardDropdown.contains(event.target)) {
            dashboardDropdownContent.classList.remove('show');
            dashboardDropdown.querySelector('.fa-caret-down').style.transform = 'rotate(0)';
        }
    });
    
    // Auto-ocultar alertas flash después de 5 segundos
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.classList.remove('show');
            alert.addEventListener('transitionend', function() {
                alert.remove();
            });
        }, 5000);
    });
    
    // Vista previa de la imagen al cargar en formularios
    const imageInput = document.getElementById('imagen');
    if (imageInput) {
        imageInput.addEventListener('change', function(event) {
            const preview = document.createElement('div');
            preview.className = 'image-preview mt-2';
            
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    // Eliminar vista previa anterior si existe
                    const existingPreview = document.querySelector('.image-preview');
                    if (existingPreview) {
                        existingPreview.remove();
                    }
                    
                    // Crear nueva vista previa
                    preview.innerHTML = `<img src="${e.target.result}" class="img-thumbnail" style="max-height: 150px;">
                                        <div class="form-text">Vista previa</div>`;
                    
                    // Agregar después del input
                    imageInput.parentNode.appendChild(preview);
                }
                
                reader.readAsDataURL(this.files[0]);
            }
        });
    }
    
    // Confirmación para acciones importantes
    const deleteButtons = document.querySelectorAll('.btn-delete');
    if (deleteButtons) {
        deleteButtons.forEach(function(button) {
            button.addEventListener('click', function(event) {
                if (!confirm('¿Está seguro de que desea eliminar este elemento? Esta acción no se puede deshacer.')) {
                    event.preventDefault();
                }
            });
        });
    }
}); 