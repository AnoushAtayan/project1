$(document).ready(function() {
    $('#submit_search').prop('disabled', true);
    $('#book').keyup(function() {
        $('#submit_search').prop('disabled', this.value == "" ? true : false);
    })

    $('input[type=radio]').change(function() {
         $('#submit_review').show();
    });
});