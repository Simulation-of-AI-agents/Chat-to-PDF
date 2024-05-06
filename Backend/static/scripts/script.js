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
