$(document).ready(function() {
    $('.delete-button').click(function(e) {
        e.preventDefault();  // Verhindert das Standardverhalten des Buttons, das die Seite neu laden würde.
        
        var container = $(this).closest('.image-container'); // Der Container, der das Bild und den Button enthält.
        var file_name = $(this).data('file-name'); // Der Dateiname wird aus dem data-file-name Attribut ausgelesen.

        // Durchführen des AJAX-Requests
        $.ajax({
            url: '/delete/' + file_name,  // Die URL für den AJAX-Request, der die Löschfunktion auf dem Server aufruft.
            type: 'GET',  // Methode des Requests
            success: function(result) {
                // Wenn der Request erfolgreich war, blende den Container aus und entferne ihn.
                container.fadeOut(400, function() {
                    $(this).remove(); // Entfernt den Container aus dem DOM nachdem das Ausblenden abgeschlossen ist.
                });
            },
            error: function(xhr, status, error) {
                // Bei einem Fehler zeige eine Fehlermeldung an.
                alert('Fehler beim Löschen der Datei: ' + error);
            }
        });
    });
});


document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('contextmenu', event => event.preventDefault());
});

document.addEventListener('DOMContentLoaded', function() {
    var uploadContainer = document.getElementById('upload-container');
    var fileInput = document.getElementById('file-input');

    uploadContainer.addEventListener('click', function() {
        fileInput.click();
    });

    uploadContainer.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadContainer.classList.add('dragover');
    });

    uploadContainer.addEventListener('dragleave', function() {
        uploadContainer.classList.remove('dragover');
    });

    uploadContainer.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadContainer.classList.remove('dragover');
        var files = e.dataTransfer.files;
        handleFiles(files);
    });

    fileInput.addEventListener('change', function() {
        var files = fileInput.files;
        handleFiles(files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            var formData = new FormData();
            formData.append('file', files[0]);

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    window.location.reload();
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while uploading the file.');
            });
        }
    }
});
