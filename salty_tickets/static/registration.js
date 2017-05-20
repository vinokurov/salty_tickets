$(document).ready(function() {
    $('button#get_total_price').on('click', function (e) {
        var url = "{{ url_for('total_price', event_key=event.event_key) }}"; // send the form data here.
        $.ajax({
            type: "POST",
            url: url,
            data: $('form').serialize(), // serializes the form's elements.
            success: function (data) {
                console.log(data)  // display the returned data in the console.
            }
        });
        e.preventDefault(); // block the traditional submission of the form.
    });
    // Inject our CSRF token into our AJAX request.
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", "{{ form.csrf_token._value() }}")
            }
        }
    })
});