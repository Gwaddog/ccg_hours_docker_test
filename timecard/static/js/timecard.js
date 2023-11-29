// see: https://mdbootstrap.com/docs/b4/jquery/tables/scroll/
$(document).ready(function () {
  $('#ph-0').DataTable({
    "scrollY": "50vh",
    "scrollCollapse": true,
  });
  $('.dataTables_length').addClass('bs-select');
});
$(document).ready(function(){         
  $(window).on("beforeunload", function(e) {
      $.ajax({
              url: 'accounts/logout/',
              method: 'GET',
          })
  });
});